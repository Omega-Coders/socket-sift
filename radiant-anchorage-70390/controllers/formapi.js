const formapi=  require('../models/form_api');
const{StatusCodes}=require("http-status-codes");
const {BadRequestError,NotFoundError}=require("../errors");
const { FormInfo } = require('../models/form_api')
// const create=async(req,res)=>{
//     await formapi.create({NameofPublisher:"hello", PublisherEmail:"sundar@gmail.com",
//     NameofTemplate:"midtemplate",TypeofTemplate:"mid paper"}),res.send("helloworld");
// }

const createform =async(req,res)=>{
    //req.body.createdBy = req.user.userId
           const task= await formapi.create(req.body)

        res.status(StatusCodes.CREATED).json(task);
        
    }

const getallforminfo = async (req,res)=>{
    try {
        const detail = await formapi.find();
        return res.status(200).json({detail});
    }catch(error) {
        return res.status(404).json({message: error.message});
    }
}

const getforminfo =(req,res)=>{
    res.send("getforminfo");
}
module.exports={createform,getallforminfo,getforminfo};