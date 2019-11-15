from allure_commons._allure import attach
from allure_commons.types import AttachmentType

def after_scenario(context, scenario):
    # Attaching image
    f = open('./files/fescobar.png', "rb")
    image = f.read()
    attach(image, name='image', attachment_type=AttachmentType.PNG)

    # Attaching video
    f = open('./files/google.mp4', "rb")
    video = f.read()
    attach(video, name='video', attachment_type=AttachmentType.MP4)