
import numpy as np
from django.db import models



class Photographer(models.Model):
    name = models.CharField(max_length=100)
    password = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    secret = models.CharField(max_length=100)



class Event(models.Model):
    name = models.CharField(max_length=100)
    date = models.CharField(max_length=100)
    directory_path = models.CharField(max_length=255)
    location = models.CharField(max_length=100)
    qr_path = models.CharField(max_length=255)
    photographer = models.ForeignKey(Photographer, on_delete=models.CASCADE, related_name='events')


class Guest(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='guests', null=True, blank=True)
    stage = models.IntegerField(default=0)


class SelfieImage(models.Model):
    selfi_encode = models.BinaryField()
    guest = models.OneToOneField(Guest, on_delete=models.CASCADE, related_name='selfie_image')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='selfie_images', null=True, blank=True)

    def set_encoding(self, encoding_array):
        self.selfi_encode = np.array(encoding_array, dtype=np.float32).tobytes()

    def get_encoding(self):
        return np.frombuffer(self.selfi_encode, dtype=np.float32)


class EventImage(models.Model):
    path = models.CharField(max_length=255)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='event_event_images', null=True, blank=True)
    is_classified = models.BooleanField(default=False)


class ImageGroup(models.Model):
    face_encode = models.BinaryField()
    guest = models.ForeignKey(Guest, on_delete=models.CASCADE, related_name='image_groups', null=True, blank=True)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='event_image_groups', null=True, blank=True)

    def set_encoding(self, encoding_array):
        self.face_encode = np.array(encoding_array, dtype=np.float32).tobytes()

    def get_encoding(self):
        return np.frombuffer(self.face_encode, dtype=np.float32)

    def is_same_person(self, other_face_encode, threshold=0.45):
        distance = np.linalg.norm(self.get_encoding() - other_face_encode)
        print(f"Distance: {distance}")
        return distance < threshold


class EventImageToImageGroup(models.Model):
    event_image = models.ForeignKey(EventImage, on_delete=models.CASCADE, related_name='event_image_to_groups')
    image_group = models.ForeignKey(ImageGroup, on_delete=models.CASCADE, related_name='image_group_to_event_images')
    sent = models.BooleanField(default=False)
