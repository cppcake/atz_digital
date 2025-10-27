# Most of this file has been generated using GitHub CoPilot with GPT-4.1

import os
import time
import json
import base64
import sqlite3
import asyncio
import datetime
from PIL import Image
from uuid import UUID
from io import BytesIO
from db.topic import Answer, Statement, Topic, TopicDB
from fastapi import FastAPI, HTTPException, Request, WebSocket
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import List

ALLOWED_COLORS = {"green", "yellow", "red", "blue", "purple"}
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.join(BASE_DIR, "web")

templates = Jinja2Templates(directory="web")

app = FastAPI()
app.mount("/web", StaticFiles(directory=WEB_DIR), name="web")


@app.on_event("startup")
def startup():
    _ = TopicDB()
    app.state.phase = 0
    app.state.topic = {}
    app.state.current_statement = 0
    app.state.players = []
    app.state.survey = {}
    app.state.delayed_answers = False
    app.state.notes = ""


@app.get("/")
async def render_frontpage(request: Request):
    return templates.TemplateResponse(
        "admin/frontpage.html", {
            "request": request}
    )


@app.get("/topic/overview")
async def render_topics(request: Request):
    topics = []

    try:
        topics = [{"id": str(t.id), "content": t.content}
                  for t in Topic.list_all()]
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=str(e))

    return templates.TemplateResponse(
        "admin/topic/overview/overview.html", {
            "request": request, "topics": topics}
    )


@app.get("/topic/select/{id}")
async def render_topic_select(request: Request, id: str):
    topic_versions = []

    try:
        topic_versions = [t.as_dict()
                          for t in Topic.get_all_versions(UUID(id))]
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=str(e))

    return templates.TemplateResponse(
        "admin/topic/select/select.html",
        {"request": request, "topic_versions": topic_versions, "id": id},
    )


@app.get("/topic/edit/{id}")
async def render_topic_edit(request: Request, id):
    def get_answer(key: str, answers):
        for a in answers:
            if a["color"].lower().strip() == key.lower().strip():
                return a["content"]

        return ""

    try:
        topic = Topic.get_newest_version(UUID(id))
        context = topic.as_dict()

        context["green"] = get_answer("green", context["answers"])
        context["yellow"] = get_answer("yellow", context["answers"])
        context["red"] = get_answer("red", context["answers"])
        context["blue"] = get_answer("blue", context["answers"])
        context["purple"] = get_answer("purple", context["answers"])
        context["request"] = request
        context["image_names"] = await get_images()
        print(context)
        return templates.TemplateResponse("admin/topic/put/edit/edit.html", context)
    except Exception as e:
        print(e)
        return templates.TemplateResponse(
            "admin/topic/put/edit/not_found.html", {"request": request}
        )


@app.post("/topic/edit/{id}")
async def topic_edit(request: Request, id):
    """
    Expects a JSON in the Payload with the following structure:

    {
        "content": "Climate change",
        "statements": ["Climate change is manmade", "Climate change is bad", "Animals are suffering because of climate change"],
        "answers": {
            "green": ["Yes", IMG.PNG],
            "yellow": ["Maybe", IMG.PNG],
            "red": ["No", IMG.PNG],
        }
    }

    Using this JSON it updates the topic with the id {id}.
    """

    # Parse data from json and provide default values in case of missing data.
    data = await request.json()
    content = data.get("content", "Neues Thema")
    statements = data.get("statements", [])
    answers = data.get("answers", {})

    # Create the topic entity
    topic = Topic(version=0, content=content, id=UUID(id))

    # Set the correct topic version
    try:
        # Get the old topics version again instead of passing it to the request to minimize the risk of concurrent updates messing up the versioning
        old_version = Topic.get_newest_version(id).version
        # And update this topics version
        topic.version = old_version + 1

    except Exception as e:
        return JSONResponse({"status": "error", "detail": str(e)}, status_code=400)

    # Create a list of statement entities, ordering them by their position in the json list.
    statements = [
        Statement(topic_id=topic.id, topic_version=topic.version,
                  content=c, position=p)
        for p, c in enumerate(statements)
        if c  # The text content c should not be empty
    ]

    # Create a list of answer entities and filter out any invalid answers. A answer is invalid if its text content is empty or if it has a invalid color.
    answers = [
        Answer(
            topic_id=topic.id,
            topic_version=topic.version,
            content=ar[0],
            color=col.lower(),
            icon=ar[1],
        )
        for col, ar in answers.items()
        if col.lower() in ALLOWED_COLORS and content
    ]

    # Try and insert all entities into the database
    try:
        topic.insert()

        for answer in answers:
            answer.insert()

        for statement in statements:
            statement.insert()

    except Exception as e:
        return JSONResponse({"status": "error", "detail": str(e)}, status_code=400)

    return JSONResponse({"status": "success", "topic_id": str(topic.id)})


@app.put("/topic/ignore/{id}")
async def topic_ignore(request: Request, id):
    try:
        topic = Topic.fetch(id, 0)
        topic.set_ignored(True)
    except Exception as e:
        return JSONResponse({"status": "error", "detail": str(e)}, status_code=400)

    return JSONResponse({"status": "success"})


@app.get("/topic/create")
async def render_topic_create(request: Request):
    return templates.TemplateResponse(
        "admin/topic/put/create/create.html",
        {"image_names": await get_images(), "request": request},
    )


async def get_images():
    # List all PNG files in /web/imgs/answers/
    imgs_dir = os.path.join(WEB_DIR, "imgs", "answers")
    try:
        image_names = [
            os.path.splitext(f)[0]  # Remove .png extension
            for f in os.listdir(imgs_dir)
            if (
                f.lower().endswith(".png")
                and os.path.isfile(os.path.join(imgs_dir, f))
                and f.lower() != "missing.png"
            )
        ]
    except Exception:
        image_names = []
    return image_names


@app.get("/imgs/answers")
async def get_imgs_answers():
    # Returns a Json containing a dict that maps every image name in /web/imgs/answers (without the .png extension!) to its base64 decoded
    imgs_dir = os.path.join(WEB_DIR, "imgs", "answers")
    result = {}
    try:
        for f in os.listdir(imgs_dir):
            if (
                f.lower().endswith(".png")
                and os.path.isfile(os.path.join(imgs_dir, f))
                and f.lower() != "missing.png"
            ):
                name = os.path.splitext(f)[0]
                with open(os.path.join(imgs_dir, f), "rb") as img_file:
                    b64 = base64.b64encode(img_file.read()).decode("utf-8")
                    result[name] = b64
    except Exception as e:
        return JSONResponse({"status": "error", "detail": str(e)}, status_code=500)
    return JSONResponse(result)


@app.get("/imgs/players")
async def get_imgs_players():
    # Returns a JSON mapping every image name in /web/imgs/players (without .png) to its base64 encoding
    imgs_dir = os.path.join(WEB_DIR, "imgs", "players")
    result = {}
    try:
        for f in os.listdir(imgs_dir):
            if (
                f.lower().endswith(".png")
                and os.path.isfile(os.path.join(imgs_dir, f))
                and f.lower() != "missing.png"
            ):
                name = os.path.splitext(f)[0]
                with open(os.path.join(imgs_dir, f), "rb") as img_file:
                    b64 = base64.b64encode(img_file.read()).decode("utf-8")
                    result[name] = b64
    except Exception as e:
        return JSONResponse({"status": "error", "detail": str(e)}, status_code=500)
    return JSONResponse(result)


@app.post("/topic/create")
async def topic_create(request: Request):
    """
    Expects a JSON in the Payload with the following structure:

    {
        "content": "Climate change",
        "statements": ["Climate change is manmade", "Climate change is bad", "Animals are suffering because of climate change"],
        "answers": {
            "green": ["Yes", "BILD"],
            "yellow": ["Maybe", "BILD"],
            "red": ["No", "BILD"]
        }
    }

    Using this JSON it creates a new topic.
    """
    # Parse data from json and provide default values in case of missing data.
    data = await request.json()
    content = data.get("content", "Neues Thema")
    statements = data.get("statements", [])
    answers = data.get("answers", {})

    # Create the topic entity
    topic = Topic(version=0, content=content)

    # Create a list of statement entities, ordering them by their position in the json list.
    statements = [
        Statement(topic_id=topic.id, topic_version=topic.version,
                  content=c, position=p)
        for p, c in enumerate(statements)
        if c  # The text content c should not be empty
    ]

    # Create a list of answer entities and filter out any invalid answers. A answer is invalid if its text content is empty or if it has a invalid color.
    answers = [
        Answer(
            topic_id=topic.id,
            topic_version=topic.version,
            content=ar[0],
            color=col.lower(),
            icon=ar[1],
        )
        for col, ar in answers.items()
        if col.lower() in ALLOWED_COLORS and content
    ]

    # Try and insert all entities into the database
    try:
        topic.insert()

        for answer in answers:
            answer.insert()

        for statement in statements:
            statement.insert()

    except Exception as e:
        return JSONResponse({"status": "error", "detail": str(e)}, status_code=400)

    return JSONResponse({"status": "success", "topic_id": str(topic.id)})


@app.post("/image/upload")
async def image_upload(request: Request):
    '''
    Expects a JSON in the Payload with the following structure:

    {
        "images": ["BASE64 ENCODING OF THE IMAGE", "BASE64 ENCODING OF THE IMAGE"]
    }

    For each base64-encoded image it does the following: First it decodes the image, then it converst the image to PNG, then it saves the image in /web/imgs/answers
    '''
    data = await request.json()
    images = data.get("images", [])
    saved_files = []
    imgs_dir = os.path.join(WEB_DIR, "imgs", "answers")
    os.makedirs(imgs_dir, exist_ok=True)

    for idx, img_b64 in enumerate(images):
        try:
            img_bytes = base64.b64decode(img_b64)
            img = Image.open(BytesIO(img_bytes)).convert("RGBA")
            # Resize if width > 720 or height > 720, keep aspect ratio
            max_width = 480
            max_height = 480
            width, height = img.width, img.height
            scale = min(max_width / width, max_height / height, 1.0)
            if scale < 1.0:
                new_size = (int(width * scale), int(height * scale))
                img = img.resize(new_size, Image.LANCZOS)
            filename = f"{datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')}_{idx}.png"
            filepath = os.path.join(imgs_dir, filename)
            img.save(filepath, format="PNG", optimize=True, compress_level=6)
            saved_files.append(filename)
        except Exception as e:
            print(f"Image upload error: {e}")

    return JSONResponse({"status": "success", "files": saved_files})


@app.post("/image/upload_players")
async def image_upload_players(request: Request):
    '''
    Expects a JSON in the Payload with the following structure:

    {
        "images": ["BASE64 ENCODING OF THE IMAGE", ...]
    }

    For each base64-encoded image it decodes, converts to PNG, and saves in /web/imgs/players
    '''
    data = await request.json()
    images = data.get("images", [])
    saved_files = []
    imgs_dir = os.path.join(WEB_DIR, "imgs", "players")
    os.makedirs(imgs_dir, exist_ok=True)

    for idx, img_b64 in enumerate(images):
        try:
            img_bytes = base64.b64decode(img_b64)
            img = Image.open(BytesIO(img_bytes)).convert("RGBA")
            # Resize if width > 480 or height > 480, keep aspect ratio
            max_width = 480
            max_height = 480
            width, height = img.width, img.height
            scale = min(max_width / width, max_height / height, 1.0)
            if scale < 1.0:
                new_size = (int(width * scale), int(height * scale))
                img = img.resize(new_size, Image.LANCZOS)
            filename = f"{datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')}_{idx}.png"
            filepath = os.path.join(imgs_dir, filename)
            img.save(filepath, format="PNG", optimize=True, compress_level=6)
            saved_files.append(filename)
        except Exception as e:
            print(f"Image upload error: {e}")

    return JSONResponse({"status": "success", "files": saved_files})


def parse_ts(ts: str) -> {}:
    return {
        "timestamp": ts,
        "year": ts[0:4],
        "month": ts[4:6],
        "day": ts[6:8],
        "hour": ts[9:11],
        "min": ts[11:13],
        "sec": ts[13:15],
    }


async def get_sessions() -> [{}]:
    session_dir = "./sessions"

    files = [
        (
            parse_ts(path.split(".")[0]),
            os.path.join(session_dir, path),
        )
        for path in os.listdir(session_dir)
        if path.lower().strip().endswith(".json")
    ]

    session_data = []

    for date, path in files:
        with open(path, "r") as f:
            try:
                data = json.load(f)
                data["date"] = date
                session_data.append(data)
            except Exception:
                print(f"ERR: Failed to parse session json: '{path}'")

    session_data_sorted_by_date = sorted(
        session_data,
        key=lambda x: x["date"]["timestamp"],
        reverse=True
    )

    return session_data_sorted_by_date


@app.get("/sessions")
async def render_sessions(request: Request):
    sessions = await get_sessions()
    return templates.TemplateResponse(
        "admin/sessions/sessions.html", {"request": request,
                                         "sessions": sessions}
    )


@app.get("/sessions/{filename}")
async def render_session_details(request: Request, filename: str):
    sessions_dir = os.path.join(BASE_DIR, "sessions")
    session_path = os.path.join(sessions_dir, filename + ".json")
    session_dict = {}
    try:
        with open(session_path, "r", encoding="utf-8") as f:
            session_dict = json.load(f)
            session_dict["date"] = parse_ts(filename)
    except Exception as e:
        print(f"File {session_path} not found")

    return templates.TemplateResponse(
        "admin/sessions/details/details.html",
        {"request": request, "session_dict": session_dict},
    )


@app.delete("/sessions/{filename}")
async def move_session(request: Request, filename: str):
    """Move a session file to the trash-bin folder instead of deleting it permanently."""
    try:
        # Define source and destination paths
        sessions_dir = os.path.join(BASE_DIR, "sessions")
        source_path = os.path.join(sessions_dir, f"{filename}.json")
        trash_bin_dir = os.path.join(sessions_dir, "trash-bin")

        # Create trash-bin directory if it doesn't exist
        os.makedirs(trash_bin_dir, exist_ok=True)

        # Destination path in trash-bin folder
        dest_path = os.path.join(trash_bin_dir, f"{filename}.json")

        # Check if the file exists
        if not os.path.exists(source_path):
            return JSONResponse(
                {"status": "error", "detail": "Session file not found"},
                status_code=404
            )

        # Move the file (rename operation in Python)
        os.rename(source_path, dest_path)

        return JSONResponse({"status": "success", "detail": "Session moved to trash-bin"})

    except Exception as e:
        print(f"Error moving session to trash-bin: {e}")
        return JSONResponse(
            {"status": "error", "detail": str(e)},
            status_code=500
        )


@app.get("/topic/stats/{topic_id}")
async def render_topic_stats(request: Request, topic_id: str):
    sessions_dir = os.path.join(BASE_DIR, "sessions")
    sessions = []
    topic_dict = Topic.get_newest_version(UUID(topic_id)).as_dict()
    fnames = []
    if os.path.isdir(sessions_dir):
        for fname in os.listdir(sessions_dir):
            if fname.endswith(".json"):
                session_path = os.path.join(sessions_dir, fname)
                try:
                    with open(session_path, "r", encoding="utf-8") as f:
                        session_data = json.load(f)
                        if (
                            "topic" in session_data and
                            "id" in session_data["topic"] and
                            str(session_data["topic"]["id"]) == str(topic_id)
                        ):
                            sessions.append(session_data)
                            fnames.append(fname)
                except Exception as e:
                    print(f"Failed to load session {fname}: {e}")
    return templates.TemplateResponse(
        "admin/topic/stats/stats.html",
        {"request": request, "sessions": sessions, "topic": topic_dict,
            "id": topic_dict["id"], "session_names": [fnames]},
    )


@app.get("/therapy/prepare/{topic_id}/{topic_version}")
async def render_therapy_prepare(request: Request, topic_id: str, topic_version: int):
    topic = {}

    try:
        topic = Topic.fetch(topic_id, topic_version).as_dict()
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=str(e))

    return templates.TemplateResponse(
        "admin/therapy/prepare/prepare.html", {
            "request": request, "topic": topic}
    )


@app.get("/therapy/navigation")
async def render_therapy_prepare(request: Request):
    if app.state.phase == 1:
        return templates.TemplateResponse(
            "admin/therapy/navigation/navigation.html", {"request": request}
        )
    else:
        return templates.TemplateResponse(
            "admin/therapy/ups/ups.html", {"request": request})


@app.get("/therapy/end")
async def render_therapy_end(request: Request):
    return templates.TemplateResponse(
        "admin/therapy/end/end.html", {"request": request}
    )


@app.get("/therapy/notes")
async def render_theray_notes(request: Request):
    if app.state.phase == 1:
        state_dict = {
            "phase": app.state.phase,
            "topic": app.state.topic,
            "current_statement": app.state.current_statement,
            "players": app.state.players,
            "delayed_answers": app.state.delayed_answers,
            "notes": app.state.notes
        }

        return templates.TemplateResponse(
            "admin/therapy/notes/notes.html",
            {"request": request, "session_dict": state_dict},
        )
    else:
        return templates.TemplateResponse("admin/therapy/ups/ups.html", {"request": request})


@app.put("/therapy/notes/")
async def save_notes(request: Request):
    try:
        data = await request.json()
        notes = data.get("notes", "")
        # Only allow saving notes while in therapy phase 1 (optional, mirrors other endpoints)
        if app.state.phase != 1:
            return JSONResponse({"status": "error", "detail": "wrong_phase"}, status_code=403)
        app.state.notes = notes
        return JSONResponse({"status": "success"})
    except Exception as e:
        return JSONResponse({"status": "error", "detail": str(e)}, status_code=400)


@app.get("/therapy/survey")
async def render_therapy_survey(request: Request):
    if app.state.phase == 1:
        return templates.TemplateResponse(
            "admin/therapy/survey/survey.html", {"request": request}
        )
    else:
        return templates.TemplateResponse(
            "admin/therapy/ups/ups.html", {"request": request}
        )


@app.get("/therapy/thanks")
async def render_theray_thanks(request: Request):
    if app.state.phase == 1:
        return templates.TemplateResponse(
            "admin/therapy/thanks/thanks.html", {"request": request}
        )
    else:
        return templates.TemplateResponse(
            "admin/therapy/ups/ups.html", {"request": request}
        )


@app.get("/therapy/ups")
async def render_theray_ups(request: Request):
    return templates.TemplateResponse(
        "admin/therapy/ups/ups.html", {"request": request}
    )


@app.get("/therapy/state")
async def therapy_state(request: Request) -> dict:
    try:
        state_dict = {
            "phase": app.state.phase,
            "topic": app.state.topic,
            "current_statement": app.state.current_statement,
            "players": app.state.players,
            "delayed_answers": app.state.delayed_answers,
            "notes": getattr(app.state, "notes", "")
        }
        return state_dict
    except Exception as e:
        print(e)
        return JSONResponse({"status": "error", "detail": str(e)}, status_code=400)


@app.get("/therapy/state/phase")
async def therapy_state_phase(request: Request) -> int:
    try:
        return app.state.phase
    except Exception as e:
        print(e)
        return JSONResponse({"status": "error", "detail": str(e)}, status_code=400)


@app.put("/therapy/survey")
async def therapy_survey(request: Request):
    try:
        data = await request.json()
        app.state.survey = data
        return JSONResponse({"status": "success"})
    except Exception as e:
        return JSONResponse({"status": "error", "detail": str(e)}, status_code=400)


@app.put("/therapy/start/{topic_id}/{topic_version}")
async def therapy_start(request: Request, topic_id: str, topic_version: int):
    try:
        app.state.phase = 1
        app.state.topic = Topic.fetch(topic_id, topic_version).as_dict()
        color_order = ["green", "yellow", "red", "blue", "purple"]
        new_answers = []
        for i in range(len(color_order)):
            for answer in app.state.topic["answers"]:
                if answer["color"] == color_order[i]:
                    new_answers.append(answer)
        app.state.topic["answers"] = new_answers

        app.state.current_statement = 0

        data = await request.json()
        app.state.players = data.get("players", [])
        app.state.delayed_answers = data.get("delayed_answers", False)
        app.state.notes = ""
        num_statements = len(app.state.topic.get("statements", []))
        for player in app.state.players:
            player["answers"] = ["None" for _ in range(num_statements)]
            player["answer_times"] = [0.0 for _ in range(num_statements)]
        app.state.statement_start_time = time.time()
        await notify_change({"type": "phase", "data": {"phase": app.state.phase}})
    except Exception as e:
        print(e)
        return JSONResponse({"status": "error", "detail": str(e)}, status_code=400)


@app.put("/therapy/forward")
async def therapy_forward(request: Request):
    if app.state.phase == 1:
        if app.state.current_statement < len(app.state.topic.get("statements", [])) - 1:
            app.state.current_statement += 1
            app.state.statement_start_time = time.time()
            # Reset timer only for players who haven't answered yet
            for player in app.state.players:
                if player["answers"][app.state.current_statement] == "None":
                    player["answer_times"][app.state.current_statement] = 0.0
            await notify_change(
                {
                    "type": "jump_statement",
                    "data": {"current_statement": app.state.current_statement},
                }
            )
            return JSONResponse({"status": "success"})
        return JSONResponse(
            {"status": "error", "detail": "max_reached"}, status_code=403
        )
    return JSONResponse({"status": "error", "detail": "wrong_phase"}, status_code=403)


@app.put("/therapy/backward")
async def therapy_backward(request: Request):
    if app.state.phase == 1:
        if app.state.current_statement > 0:
            app.state.current_statement -= 1
            app.state.statement_start_time = time.time()
            for player in app.state.players:
                if player["answers"][app.state.current_statement] == "None":
                    player["answer_times"][app.state.current_statement] = 0.0
            await notify_change(
                {
                    "type": "jump_statement",
                    "data": {"current_statement": app.state.current_statement},
                }
            )
            return JSONResponse({"status": "success"})
        return JSONResponse(
            {"status": "error", "detail": "min_reached"}, status_code=403
        )
    return JSONResponse({"status": "error", "detail": "wrong_phase"}, status_code=403)


@app.put("/therapy/jump/{statement_nr}")
async def therapy_jump(request: Request, statement_nr: int):
    if app.state.phase == 1:
        num_statements = len(app.state.topic.get("statements", []))
        if 0 <= statement_nr < num_statements:
            app.state.current_statement = statement_nr
            app.state.statement_start_time = time.time()
            for player in app.state.players:
                if player["answers"][app.state.current_statement] == "None":
                    player["answer_times"][app.state.current_statement] = 0.0
            await notify_change(
                {
                    "type": "jump_statement",
                    "data": {"current_statement": app.state.current_statement},
                }
            )
            return JSONResponse({"status": "success"})
        return JSONResponse(
            {"status": "error", "detail": "out_of_bounds"}, status_code=403
        )
    return JSONResponse({"status": "error", "detail": "wrong_phase"}, status_code=403)


@app.put("/therapy/vote/{remote_id}/{color}")
async def therapy_vote(request: Request, remote_id: int, color: str):
    try:
        colors = [a["color"] for a in app.state.topic["answers"]]
        if app.state.phase == 1:
            for player in app.state.players:
                if player["id"] == remote_id and color in colors:
                    if player["answers"][app.state.current_statement] == color:
                        return
                        color = "None"
                    # Only set time if not already set
                    if player["answer_times"][app.state.current_statement] == 0.0:
                        elapsed = time.time() - getattr(app.state, "statement_start_time", time.time())
                        player["answer_times"][app.state.current_statement] = elapsed
                    player["answers"][app.state.current_statement] = color
                    await notify_change(
                        {
                            "type": "vote",
                            "data": {"remote_id": remote_id, "color": color},
                        }
                    )
                    return JSONResponse({"status": "ok"})
            return JSONResponse(
                {"status": "error", "detail": "remote not in therapy or unmapped color choosen!"}, status_code=403
            )
        else:
            return JSONResponse(
                {"status": "error", "detail": "wrong_phase"}, status_code=403
            )
    except KeyError:
        return JSONResponse(
            {"status": "error", "detail": "no answers"}, status_code=403
        )
    except Exception as e:
        print(e)
        return JSONResponse({"status": "error", "detail": str(e)}, status_code=400)


@app.put("/therapy/end")
async def therapy_end(request: Request):
    try:
        if app.state.phase == 1:
            # Save stats
            session_data = {
                "phase": app.state.phase,
                "topic": app.state.topic,
                "current_statement": app.state.current_statement,
                "players": app.state.players,
                "survey": app.state.survey,
                "notes": app.state.notes,
            }
            sessions_dir = os.path.join(BASE_DIR, "sessions")
            os.makedirs(sessions_dir, exist_ok=True)
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            session_filename = f"{timestamp}.json"
            session_path = os.path.join(sessions_dir, session_filename)
            with open(session_path, "w", encoding="utf-8") as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)

            # Reset stats
            app.state.phase = 0
            app.state.topic = {}
            app.state.current_statement = 0
            app.state.players = []
            app.state.survey = {}
            app.state.delayed_answers = False
            app.state.notes = ""
            await notify_change({"type": "phase", "data": {"phase": app.state.phase}})
        else:
            return JSONResponse(
                {"status": "error", "detail": "wrong_phase"}, status_code=403
            )
    except Exception as e:
        print(e)
        return JSONResponse({"status": "error", "detail": str(e)}, status_code=400)


@app.get("/visualizer")
def visualizer(request: Request):
    return templates.TemplateResponse(
        "visualizer/visualizer.html", {"request": request}
    )


"""
Websocket API
"""

i: int = 0
change_queues: List[List[dict]] = []


@app.websocket("/subscribe_change")
async def subscribe_change(websocket: WebSocket):
    global i
    my_index: int = i
    change_queues.append([])
    i += 1
    await websocket.accept()
    try:
        while True:
            if change_queues[my_index]:
                change = change_queues[my_index].pop()
                await websocket.send_json(change)
            await asyncio.sleep(0.25)
    except Exception as e:
        print(e)


async def notify_change(change: dict):
    global change_queues
    for queue in change_queues:
        queue.append(change)


"""
Debug API
"""

@app.get("/debug/remote")
async def render_debug_remote(request: Request):
    return templates.TemplateResponse("debug/remote/remote.html", {"request": request})


@app.get("/debug/websocket")
async def render_debug_websocket(request: Request):
    return templates.TemplateResponse(
        "debug/websocket/websocket.html", {"request": request}
    )


@app.get("/topic/details/{topic_uuid}/{version}")
async def topic_details(request: Request, topic_uuid: str, version: int):
    return Topic.fetch(topic_uuid, version).as_dict()


@app.get("/topic/details/{topic_id}")
async def topic_details_all_versions(request: Request, topic_id: str):
    """Returns a json response containing all versions of this topic"""

    try:
        return [t.as_dict() for t in Topic.get_all_versions(UUID(topic_id))]

    except Exception:
        return JSONResponse(
            {"status": "error", "detail": "No such topic"}, status_code=404
        )


@app.get("/visualizer/debug")
def visualizer_debug(request: Request):
    return templates.TemplateResponse(
        "visualizer/visualizer.html", {"request": request, "debug": True}
    )
