import time

import face_recognition

from sklearn.cluster import DBSCAN

from core.models import EventImageToImageGroup, EventImage, ImageGroup, Event
from photos_sender.sender_bot import send_images_to_all
from thread_manager import submit_task, get_faces, force_shutdown, get_encodings
import logging
import logging_config

logger = logging.getLogger(__name__)


def extract_faces_and_features(image_paths):
    """Extract face encodings and paths from a list of image paths."""
    try:
        face_encodings = []
        image_faces_paths = []
        for image_path in image_paths:
            if force_shutdown():
                return
            image, face_locations = get_faces(image_path)
            logger.info("num of faces: " + str(len(face_locations)) + " at " + image_path)
            if not face_locations:
                logger.info(f"No faces found in image: {image_path}")
                img = EventImage.objects.get(path=image_path)
                img.is_classified = True
                img.save()
                continue
            encodings = get_encodings(image, face_locations)
            for encoding in encodings:
                face_encodings.append(encoding)
                image_faces_paths.append(image_path)
        return face_encodings, image_faces_paths
    except Exception as e:
        print(e)


def cluster_faces(face_encodings):
    """Cluster face encodings using DBSCAN."""
    clustering_model = DBSCAN(eps=0.427, min_samples=1, metric="euclidean")
    cluster_labels = clustering_model.fit_predict(face_encodings)
    return cluster_labels


def create_clusters_dictionary(face_encodings, cluster_labels, image_paths):
    """Create a dictionary of clusters containing the core face and associated images."""
    clusters = {}
    for idx, label in enumerate(cluster_labels):
        if label not in clusters:
            clusters[label] = {
                'core_face': face_encodings[idx],
                'image_paths': []
            }
        clusters[label]['image_paths'].append(image_paths[idx])
    clusters_list = list(clusters.values())
    return clusters_list


def add_image_to_group(paths, image_group):
    image_to_group_lst = []

    for path in paths:
        event_image = EventImage.objects.get(path=path)
        event_image.is_classified = True
        event_image.save()
        image_to_group = EventImageToImageGroup(event_image=event_image, image_group=image_group)
        image_to_group_lst.append(image_to_group)

    EventImageToImageGroup.objects.bulk_create(image_to_group_lst)


def check_existing_clusters(clusters, ids_core, event):
    for cluster in clusters:
        exist = False
        for core in ids_core:
            if core.is_same_person(cluster['core_face']):
                exist = True
                add_image_to_group(cluster['image_paths'], core)
                break
        if not exist:
            group = ImageGroup(event=event)
            group.set_encoding(cluster['core_face'])
            group.save()
            add_image_to_group(cluster['image_paths'], group)


def classify_faces(event, paths):
    logger.info("start classifying for : " + event.name)
    face_encodings, image_faces_paths = extract_faces_and_features(paths)
    print("1")
    if face_encodings:
        cluster_labels = cluster_faces(face_encodings)
        print("2")
        clusters = create_clusters_dictionary(face_encodings, cluster_labels, image_faces_paths)
        print("3")
        event_ids_core = ImageGroup.objects.filter(event=event).all()
        print("4")
        check_existing_clusters(clusters, event_ids_core, event)
        print("5")
        submit_task(send_images_to_all)


def get_unclassified_photos():
    logger.info("start classify all")
    events = Event.objects.filter(
        event_event_images__is_classified=False
    ).distinct()
    for event in events:
        paths = EventImage.objects.filter(event=event, is_classified=False).values_list('path', flat=True)
        classify_faces(event, paths)

    logger.info("all photos have been classified")
