import os
from django.core.exceptions import ValidationError

def image_validator(value):
    extention = os.path.splitext(value.name)[1]
    valid_extentions = ['.png', '.jpeg', '.jpg',]
    if extention.lower() not in valid_extentions:
        raise ValidationError('Unsupported file type, upload supported file type: '+ str(valid_extentions))
    
  
def file_validator(value):
    extention = os.path.splitext(value.name)[1]
    valid_extentions = ['.pdf', '.doc', '.docx', '.ppt', '.pptx',]

    if not extention.lower() in valid_extentions:
        raise ValidationError('Unsupported file type, upload supported file type: '+ str(valid_extentions))
    
    max_size = 5 * 1024 * 1024 
    if value.size > max_size:
        raise ValidationError('File size exceeds the maximum limit of 5MB.')
    
def video_file_validator(value):
    extention = os.path.splitext(value.name)[1]
    valid_extentions = ['.mp4', '.webm']
    
    if not extention.lower() in valid_extentions:
        raise ValidationError('Unsupported file type, upload supported file type: '+ str(valid_extentions))
    
    max_size = 20 * 1024 * 1024  
    if value.size > max_size:
        raise ValidationError('File size exceeds the maximum limit of 20MB.')
    
def combine_file_validator(value):
    try:
        file_validator(value)
    except ValidationError as e1:
        try:
            image_validator(value)
        except ValidationError as e2:
            raise ValidationError(e1, e2)
        
