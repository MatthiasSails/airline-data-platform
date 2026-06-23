VR_THRESHOLD = 1.0  # m/s deadband, avoids flicker from GPS noise during level flight

ON_GROUND_COLOR = "#9ca3af"
AIRBORNE_COLOR = "#2563eb"


def aircraft_icon_html(
    true_track: float | None,
    on_ground: bool | None,
    vertical_rate: float | None,
) -> str:
    angle = true_track if true_track is not None else 0
    is_on_ground = bool(on_ground) if on_ground is not None else False  # NULL -> airborne
    color = ON_GROUND_COLOR if is_on_ground else AIRBORNE_COLOR

    if vertical_rate is None or abs(vertical_rate) < VR_THRESHOLD:
        arrow_svg = ""
    elif vertical_rate > 0:
        arrow_svg = '<div class="vr-arrow vr-climb">&#9650;</div>'  # up triangle
    else:
        arrow_svg = '<div class="vr-arrow vr-descend">&#9660;</div>'  # down triangle

    return f'''
    <div style="position: relative; width: 32px; height: 32px;">
      <div style="transform: rotate({angle}deg); transform-origin: center;
                  width: 24px; height: 24px;">
        <svg width="24" height="24" viewBox="0 0 24 24">
          <path d="M12 2 L15 11 L22 15 L15 16 L16 22 L12 19 L8 22 L9 16 L2 15 L9 11 Z"
                fill="{color}" />
        </svg>
      </div>
      {arrow_svg}
    </div>
    '''


def vertical_trend_label(vertical_rate: float | None) -> str:
    if vertical_rate is None or abs(vertical_rate) < VR_THRESHOLD:
        return "Level"
    return "Climbing" if vertical_rate > 0 else "Descending"
