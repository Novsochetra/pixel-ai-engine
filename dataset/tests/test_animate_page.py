import io
import json
import uuid
from urllib.request import Request, urlopen

import pytest
from PIL import Image
from test_studio import site, wait_until_done  # noqa: F401  (site is a fixture)

from pixel_data.dashboard import animate_page
from pixel_data.dashboard.studio import Invalid


def sprite_png(size=(64, 64)) -> bytes:
    picture = Image.new("RGBA", size, (0, 0, 0, 0))
    picture.paste((30, 30, 200, 255), (20, 10, 44, 60))
    buffer = io.BytesIO()
    picture.save(buffer, "PNG")

    return buffer.getvalue()


def knight(data):
    folder = data / "generated" / "knight"
    folder.mkdir(parents=True)
    (folder / "generated.json").write_text(json.dumps({"prompt": "a knight with a sword", "created_at": "2026-11-22T10:00:00+00:00"}))
    for name in ("s0-front", "s0-right", "s0-front-raw", "s1-front"):
        (folder / f"{name}.png").write_bytes(sprite_png())

    return folder


def test_a_generated_character_becomes_animate_arguments(tmp_path):
    data = tmp_path
    folder = knight(data)

    title, args = animate_page.animate_job(data, {
        "source": "generated/knight", "seed": "0", "views_list": ["front", "right"], "actions_list": ["idle", "walk"],
        "size": "384", "frames": "33", "subject": "a knight,  empty hands", "same_end": "on"})

    assert title == "Animate knight: 4 clips"
    assert args[:6] == ["animate", str(folder.resolve()), "--views", "front", "right", "--seeds"]
    assert args[args.index("--actions") + 1:args.index("--size")] == ["idle", "walk"]
    assert args[args.index("--subject") + 1] == "a knight, empty hands" and "--open-end" not in args
    assert args[args.index("--name") + 1].endswith("-knight")


def test_a_character_offers_only_the_views_it_has(tmp_path):
    knight(tmp_path)

    assert animate_page.characters(tmp_path)[0]["sprites"] == {0: ["front", "right"], 1: ["front"]}
    with pytest.raises(Invalid, match="s1 has: front"):
        animate_page.animate_job(tmp_path, {"source": "generated/knight", "seed": "1", "views_list": ["right"],
                                            "actions_list": ["walk"]})


def test_an_upload_is_saved_as_a_clean_png_and_needs_a_subject(tmp_path):
    form = {"source": "upload", "facing": "right", "actions_list": ["walk"], "files": {"image": ("My Hero!.png", sprite_png((48, 64)))}}

    with pytest.raises(Invalid, match="what the picture shows"):
        animate_page.animate_job(tmp_path, form)
    title, args = animate_page.animate_job(tmp_path, {**form, "subject": "a hero in red"})

    saved = list((tmp_path / "uploads").glob("*.png"))
    assert len(saved) == 1 and saved[0].name.endswith("-my-hero.png")
    assert Image.open(saved[0]).size == (48, 64)
    assert args[:4] == ["animate", str(saved[0].resolve()), "--views", "right"] and "--open-end" in args
    assert animate_page.uploads(tmp_path) == [saved[0].name]

    # The same picture can be picked again without uploading it.
    _, again = animate_page.animate_job(tmp_path, {"source": f"uploads/{saved[0].name}", "subject": "a hero", "actions_list": ["idle"]})
    assert again[1] == str(saved[0].resolve())


@pytest.mark.parametrize("body", [b"not a picture", sprite_png((3000, 10))])
def test_a_bad_upload_is_refused(tmp_path, body):
    with pytest.raises(Invalid):
        animate_page.animate_job(tmp_path, {"source": "upload", "subject": "x", "actions_list": ["walk"],
                                            "files": {"image": ("x.png", body)}})
    assert not list((tmp_path / "uploads").glob("*.png")) if (tmp_path / "uploads").exists() else True


def test_only_known_uploads_and_actions_are_passed_on(tmp_path):
    with pytest.raises(Invalid):
        animate_page.animate_job(tmp_path, {"source": "uploads/../../etc.png", "subject": "x", "actions_list": ["walk"]})
    with pytest.raises(Invalid, match="action"):
        animate_page.animate_job(tmp_path, {"source": "upload", "subject": "x", "actions_list": ["dance"]})


def multipart(fields: list[tuple[str, str]], files: dict[str, tuple[str, bytes]]) -> tuple[bytes, str]:
    boundary = uuid.uuid4().hex
    parts = []
    for name, value in fields:
        parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode())
    for name, (filename, body) in files.items():
        parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'
                     f"Content-Type: image/png\r\n\r\n".encode() + body + b"\r\n")
    parts.append(f"--{boundary}--\r\n".encode())

    return b"".join(parts), f"multipart/form-data; boundary={boundary}"


def test_the_page_uploads_a_png_starts_the_job_and_shows_results(site):  # noqa: F811
    url, jobs = site
    data = jobs.data

    clip = data / "animated" / "old-run"
    clip.mkdir(parents=True)
    (clip / "animated.json").write_text(json.dumps({"created_at": "2026-11-23T04:57:49+00:00", "source": "knight", "size": 384,
                                                    "frames": 33, "clips": [{"id": "s0-right-walk", "used": 29}]}))
    Image.new("RGB", (8, 8)).save(clip / "s0-right-walk.gif")

    with urlopen(f"{url}/animate") as response:
        page = response.read().decode()
    assert "Animated so far" in page and "/animated/old-run/s0-right-walk.gif" in page
    assert 'href="/animate"' in page and "Upload a new PNG" in page
    with urlopen(f"{url}/animated/old-run/s0-right-walk.gif") as response:
        assert response.headers["Content-Type"] == "image/gif"
    with urlopen(f"{url}/generate") as response:
        assert "/animate?source=generated%2Ffrog" in response.read().decode()

    body, kind = multipart([("source", "upload"), ("subject", "a hero"), ("facing", "front"), ("actions", "idle"),
                            ("actions", "walk"), ("size", "384"), ("frames", "17"), ("same_end", "on")],
                           {"image": ("hero.png", sprite_png())})
    request = Request(f"{url}/animate", data=body, method="POST", headers={"Content-Type": kind, "Origin": url})
    with urlopen(request) as response:
        assert response.status == 200

    job = wait_until_done(jobs)
    assert job["title"] == "Animate " + job["args"][1].rsplit("/", 1)[-1][:-4] + ": 2 clips"
    assert job["args"][job["args"].index("--actions") + 1:job["args"].index("--size")] == ["idle", "walk"]
    assert len(list((data / "uploads").glob("*.png"))) == 1
