from ultralytics import YOLO
import torch


class YOLOPredictor:
    def __init__(self, weights_path: str, device: str | None = None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model = YOLO(weights_path)

    def predict(
        self,
        source: str,
        conf: float = 0.25,
        save: bool = False,
        project: str = "runs/",
        name: str = "exp"
    ):
        results = self.model.predict(
            source=source,
            conf=conf,
            save=save,
            project=project,
            name=name,
            device=self.device
        )

        detections = []

        for result in results:
            image_dets = []

            if result.boxes is None:
                detections.append(image_dets)
                continue

            boxes = result.boxes

            for xyxy, cls_id, score in zip(
                boxes.xyxy.cpu().numpy(),
                boxes.cls.cpu().numpy(),
                boxes.conf.cpu().numpy()
            ):
                image_dets.append({
                    "label": result.names[int(cls_id)],
                    "class_id": int(cls_id),
                    "confidence": float(score),
                    "bbox_xyxy": xyxy.tolist()
                })

            detections.append(image_dets)

        return detections
