
import socketio
import uvicorn
import numpy as np
import cv2 as cv
from PIL import Image
import io
from base64 import b64decode, b64encode
import requests
import boto3

sio = socketio.AsyncServer(cors_allowed_origins="*", async_mode="asgi", )

app = socketio.ASGIApp(sio)

@sio.event
async def connect(sid, environ):
    print('[INFO] Connect to client', sid)
    # print("request body : ", environ)

@sio.event
async def disconnect(sid):
    print('disconnect ', sid)
    

@sio.event
async def doSIFT(sid, data):
        
        s3 = boto3.resource('s3', aws_access_key_id="AKIAWEVT3WY3LBWM4LXX", aws_secret_access_key="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")


        url = "https://sift-bucket-1.s3.ap-south-1.amazonaws.com/"

        response1 = requests.get(url+data['images'][0])
        response2 = requests.get(url+data['images'][1])
        base64_data1 = str(response1.content)
        base64_data1 = base64_data1.split(',', 1)[1]
        ref_data = b64decode(base64_data1)
        pimg = Image.open(io.BytesIO(ref_data))
        pimg2 = Image.open(io.BytesIO(response2.content))

        # pimg = Image.open(pimg)
        # pimg2 = Image.open(pimg2)

        # pimg = Image.open(io.BytesIO(data1))
        # pimg2 = Image.open(io.BytesIO(data2))

        training_image = cv.cvtColor(np.array(pimg), cv.COLOR_BGR2RGB)
        test_image = cv.cvtColor(np.array(pimg2), cv.COLOR_BGR2RGB)

        training_gray = cv.cvtColor(training_image, cv.COLOR_RGB2GRAY)
        test_gray = cv.cvtColor(test_image, cv.COLOR_RGB2GRAY)

        h, w = training_gray.shape

        MIN_MATCH_COUNT = 10

        sift = cv.SIFT_create()

        kp1, des1 = sift.detectAndCompute(training_image,None)
        kp2, des2 = sift.detectAndCompute(test_image,None)

        FLANN_INDEX_KDTREE = 1

        index_params = dict(algorithm = FLANN_INDEX_KDTREE, trees = 5)
        search_params = dict(checks = 50)

        flann = cv.FlannBasedMatcher(index_params, search_params)

        matches=flann.knnMatch(np.asarray(des1,np.float32),np.asarray(des2,np.float32), 2)
        # store all the good matches as per Lowe's ratio test.
        good = []
        for m,n in matches:
            if m.distance < 0.7*n.distance:
                good.append(m)
        if len(good)>MIN_MATCH_COUNT:
            src_pts = np.float32([ kp1[m.queryIdx].pt for m in good ]).reshape(-1,1,2)
            dst_pts = np.float32([ kp2[m.trainIdx].pt for m in good ]).reshape(-1,1,2)
            M, mask = cv.findHomography(src_pts, dst_pts, cv.RANSAC,5.0)
            matchesMask = mask.ravel().tolist()
            h,w = training_gray.shape
            pts = np.float32([ [0,0],[0,h-1],[w-1,h-1],[w-1,0] ]).reshape(-1,1,2)
            dst = cv.perspectiveTransform(pts,M)
        else:
            return await sio.emit("result", {"result": "Given Image does not match to Reference Image"}, to=sid)
            # print( "Not enough matches are found - {}/{}".format(len(good), MIN_MATCH_COUNT) )
            # matchesMask = None
        
        imm = test_image.copy()

        matrix = cv.getPerspectiveTransform(dst, pts)

        destination_image = cv.warpPerspective(imm, matrix, (w, h))
        
        img = Image.fromarray(destination_image, 'RGB')

        # buffered = io.BytesIO()
        # img.save(buffered, format="JPEG")
        # img_str = b64encode(buffered.getvalue())
        # final_output = {
        #     "Transformed Image": img_str
        # }

        img.save('trans.jpeg', 'JPEG')
        

        s3.meta.client.upload_file("trans.jpeg", 'sift-bucket-1', "trans.jpeg", ExtraArgs={'ACL': 'public-read', 'ContentType': 'image/jpeg'})
        print("image is transformed")
        return await sio.emit("result", {"result": "Image Saved successfully"}, to=sid)



if __name__ == "__main__":
    config = uvicorn.Config("sift:app", port=5000, log_level="info")
    server = uvicorn.Server(config)
    server.run()

