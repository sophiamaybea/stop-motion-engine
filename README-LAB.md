# Stop Motion Lab

Runnable verification harness for dance clip → structured performance → identity-locked still frames.

## Run

    pip install -e '.[lab,dev]'
    python app/app.py

or:

    docker compose up --build

Open http://localhost:7860.

## CLI

    stopmotion analyse reference.mp4
    stopmotion beats projects/reference-01 --video reference.mp4 --annotations movement_blueprint.json --face identity_face.jpg --body identity_body.jpg
    stopmotion generate projects/reference-01 --beat 1 --adapter mock
    stopmotion validate projects/reference-01 --beat 1
    stopmotion contact-sheet projects/reference-01
    stopmotion preview projects/reference-01 --fps 3
    stopmotion doctor

mock is deliberately labelled as a structural placeholder. It never claims to retarget identity. Configure ComfyUI or REMOTE_GENERATOR_URL for the real generation pass.

The Docker image uses Python 3.11 so MediaPipe body/face/hand landmark extraction can be installed reproducibly. On runtimes where MediaPipe is absent, the app saves explicit UNAVAILABLE detector states and still completes source-frame extraction, annotations, manifests, contact sheets and project round-trips.
