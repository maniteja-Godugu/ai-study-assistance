from pydantic import BaseModel,Field,ValidationError,EmailStr
class mcq(BaseModel):
    Question:str
    options:list[str]= Field(min_length=4,max_length=4)
    correct_answer:str
    answer_explaination:str

class response_schema(BaseModel):
    defination:str
    explanation:str
    key_points:list[str]
    mcqs:list[mcq]

class input_schema(BaseModel):
    
    subject:str
    topic:str
    study_mode:str
    no_mcqs:int

class register_schema(BaseModel):
    username:str
    email:EmailStr
    password:str=Field(min_length=6)

class login_schema(BaseModel):
    email:EmailStr
    password:str