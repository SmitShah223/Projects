import cv2


def draw_label(
    image,
    text: str,
    position=(10, 40),
    bg_color=(0, 0, 0),
    text_color=(255, 255, 255),
    scale=0.8,
    thickness=2,
) -> None:
    if not text:
        return
    font = cv2.FONT_HERSHEY_SIMPLEX
    (text_width, text_height), baseline = cv2.getTextSize(text, font, scale, thickness)
    x, y = position
    cv2.rectangle(
        image,
        (x - 5, y - text_height - 5),
        (x + text_width + 5, y + baseline + 5),
        bg_color,
        -1,
    )
    cv2.putText(image, text, (x, y), font, scale, text_color, thickness, cv2.LINE_AA)


def draw_fps(image, fps: float, position=(10, 80)) -> None:
    draw_label(image, f"FPS: {fps:.1f}", position=position, bg_color=(0, 0, 0))
