const express = require("express");
const app =express();
const router=express.Router();
const {createform,getallforminfo,getforminfo}=require("../controllers/formapi")
router.route('/').get(getallforminfo).post(createform);
router.route('/:id').get(getforminfo);


module.exports=router;
