"""
FastAPI backend — Klasyfikator sampli perkusyjnych przy użyciu drzewa decyzyjnego.
Serwuje też statyczny frontend (index.html).
"""

import os, json, time, uuid, shutil, threading, numpy as np
from pathlib import Path
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from concurrent.futures import ThreadPoolExecutor
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from audio_features import extract_features, get_waveform_data, get_feature_names
from decision_tree import DecisionTreeClassifier
from metrics import evaluate_full, accuracy as calc_accuracy

app = FastAPI(title="Klasyfikator Sampli Perkusyjnych", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

BASE_DIR    = Path(__file__).parent.parent
UPLOADS_DIR = BASE_DIR / "uploads"
EXPORTS_DIR = BASE_DIR / "exports"
STATIC_DIR  = BASE_DIR / "static"
PRESETS_DIR = BASE_DIR / "presets"
UPLOADS_DIR.mkdir(exist_ok=True)
EXPORTS_DIR.mkdir(exist_ok=True)
STATIC_DIR.mkdir(exist_ok=True)
PRESETS_DIR.mkdir(exist_ok=True)

AUDIO_EXT = {".wav", ".mp3", ".flac", ".ogg", ".aiff"}

# Stan ładowania presetu (jeden na raz)
_preset_job: dict = {"phase": "idle", "preset": "", "total": 0, "done": 0, "errors": 0}
_preset_lock = threading.Lock()

state = {
    "uploaded_files": {},
    "model": None,
    "last_evaluation": None,
    "tree_params": {"criterion":"gini","max_depth":5,"min_samples_split":2,"min_samples_leaf":1},
}

class TrainParams(BaseModel):
    criterion: str = "gini"
    max_depth: int = 5
    min_samples_split: int = 2
    min_samples_leaf: int = 1
    test_split: float = 0.2

@app.get("/")
def root():
    idx = STATIC_DIR / "index.html"
    if idx.exists():
        return FileResponse(str(idx))
    return {"status": "ok", "docs": "/docs"}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...), label: str = Form(...)):
    allowed = {".wav",".mp3",".flac",".ogg",".aiff"}
    ext = Path(file.filename).suffix.lower()
    if ext not in allowed:
        raise HTTPException(400, f"Format nieobsługiwany. Dozwolone: {allowed}")
    file_id   = str(uuid.uuid4())[:8]
    save_path = UPLOADS_DIR / f"{file_id}_{file.filename}"
    with open(save_path,"wb") as f: shutil.copyfileobj(file.file, f)
    try:
        features = extract_features(str(save_path))
        waveform = get_waveform_data(str(save_path))
    except Exception as e:
        save_path.unlink(missing_ok=True)
        raise HTTPException(500, f"Błąd ekstrakcji cech: {e}")
    state["uploaded_files"][file_id] = {
        "file_id":file_id,"filename":file.filename,
        "path":str(save_path),"label":label,
        "features":features.tolist(),"waveform":waveform,
    }
    return {"file_id":file_id,"filename":file.filename,"label":label,
            "n_features":len(features),"duration_sec":waveform["duration_sec"],
            "feature_names":get_feature_names(),"features":features.tolist()}

@app.post("/upload-batch")
async def upload_batch(files: list[UploadFile] = File(...), label: str = Form(...)):
    allowed = {".wav", ".mp3", ".flac", ".ogg", ".aiff"}
    uploaded = []
    errors = 0

    def process_file(file_upload):
        ext = Path(file_upload.filename).suffix.lower()
        if ext not in allowed:
            return None
        file_id   = str(uuid.uuid4())[:8]
        save_path = UPLOADS_DIR / f"{file_id}_{file_upload.filename}"
        data = file_upload.file.read()
        with open(save_path, "wb") as f:
            f.write(data)
        try:
            features = extract_features(str(save_path))
            waveform = get_waveform_data(str(save_path))
        except Exception:
            save_path.unlink(missing_ok=True)
            return None
        entry = {
            "file_id": file_id, "filename": file_upload.filename,
            "path": str(save_path), "label": label,
            "features": features.tolist(), "waveform": waveform,
        }
        state["uploaded_files"][file_id] = entry
        return {"file_id": file_id, "filename": file_upload.filename, "label": label,
                "n_features": len(features), "duration_sec": waveform["duration_sec"],
                "feature_names": get_feature_names(), "features": features.tolist()}

    with ThreadPoolExecutor(max_workers=4) as ex:
        results = list(ex.map(process_file, files))

    for r in results:
        if r is None:
            errors += 1
        else:
            uploaded.append(r)

    return {"uploaded": len(uploaded), "errors": errors, "files": uploaded}

@app.get("/files")
def list_files():
    files = []
    for v in state["uploaded_files"].values():
        dur = v.get("duration_sec") or (v.get("waveform") or {}).get("duration_sec", 0)
        files.append({"file_id": v["file_id"], "filename": v["filename"],
                       "label": v["label"], "duration": dur})
    return {"files": files, "count": len(files)}

@app.get("/files/{file_id}")
def get_file(file_id: str):
    if file_id not in state["uploaded_files"]:
        raise HTTPException(404, "Nie znaleziono")
    v = state["uploaded_files"][file_id]
    dur = v.get("duration_sec") or (v.get("waveform") or {}).get("duration_sec", 0)
    return {
        "file_id":      v["file_id"],
        "filename":     v["filename"],
        "label":        v["label"],
        "duration_sec": dur,
        "n_features":   len(v["features"]),
        "feature_names": get_feature_names(),
        "features":     v["features"],
    }

@app.delete("/files/{file_id}")
def delete_file(file_id: str):
    if file_id not in state["uploaded_files"]:
        raise HTTPException(404,"Plik nie znaleziony")
    info = state["uploaded_files"].pop(file_id)
    Path(info["path"]).unlink(missing_ok=True)
    return {"deleted":file_id}

@app.get("/files/{file_id}/waveform")
def get_waveform(file_id: str):
    if file_id not in state["uploaded_files"]:
        raise HTTPException(404, "Nie znaleziono")
    entry = state["uploaded_files"][file_id]
    if entry.get("waveform"):
        return entry["waveform"]
    # Preset-loaded files: waveform obliczany na żądanie
    try:
        return get_waveform_data(entry["path"])
    except Exception as e:
        raise HTTPException(500, str(e))

# ──────────────────────────────────────────────────────────────────────────────
#  PRESETY
# ──────────────────────────────────────────────────────────────────────────────

def _scan_preset(preset_path: Path) -> dict[str, list[Path]]:
    """Zwraca {label: [ścieżki plików]} dla danego presetu."""
    result = {}
    for d in sorted(preset_path.iterdir()):
        if d.is_dir() and not d.name.startswith("."):
            files = sorted(f for f in d.iterdir() if f.suffix.lower() in AUDIO_EXT)
            if files:
                result[d.name] = files
    return result

@app.get("/presets")
def list_presets():
    """Lista dostępnych presetów z liczbą plików per klasa."""
    if not PRESETS_DIR.exists():
        return {"presets": []}
    presets = []
    for d in sorted(PRESETS_DIR.iterdir()):
        if not d.is_dir() or d.name.startswith("."):
            continue
        classes = _scan_preset(d)
        if not classes:
            continue
        total = sum(len(v) for v in classes.values())
        presets.append({
            "name":    d.name,
            "classes": {k: len(v) for k, v in classes.items()},
            "total":   total,
        })
    return {"presets": presets}

@app.post("/presets/{name}/load")
def load_preset(name: str):
    """Startuje ładowanie presetu w tle. Postęp: GET /presets/{name}/progress."""
    global _preset_job
    preset_path = PRESETS_DIR / name
    if not preset_path.is_dir():
        raise HTTPException(404, f"Preset '{name}' nie istnieje")
    with _preset_lock:
        if _preset_job["phase"] == "running":
            raise HTTPException(409, "Inne ładowanie już trwa")
        _preset_job = {"phase": "running", "preset": name,
                       "total": 0, "done": 0, "errors": 0}

    def _run():
        global _preset_job
        classes = _scan_preset(preset_path)
        all_files = [(str(f), label) for label, files in classes.items() for f in files]

        with _preset_lock:
            _preset_job["total"] = len(all_files)

        new_entries = {}
        errors = 0

        def process(path_label):
            path, label = path_label
            try:
                feats = extract_features(path)
                dur   = get_waveform_data(path)["duration_sec"]
                return {"path": path, "label": label,
                        "filename": Path(path).name,
                        "features": feats.tolist(),
                        "duration_sec": dur}
            except Exception:
                return None

        with ThreadPoolExecutor(max_workers=8) as ex:
            futures = {ex.submit(process, item): item for item in all_files}
            done_count = 0
            for fut in futures:
                result = fut.result()
                done_count += 1
                with _preset_lock:
                    _preset_job["done"] = done_count
                if result is None:
                    errors += 1
                    continue
                new_entries[result["path"]] = result

        # Wczytaj do state (zastąp poprzednie pliki)
        state["uploaded_files"].clear()
        for entry in new_entries.values():
            fid = str(uuid.uuid4())[:8]
            state["uploaded_files"][fid] = {
                "file_id":    fid,
                "filename":   entry["filename"],
                "path":       entry["path"],
                "label":      entry["label"],
                "features":   entry["features"],
                "duration_sec": entry["duration_sec"],
                "waveform":   None,   # obliczane na żądanie
            }

        with _preset_lock:
            _preset_job["phase"]  = "done"
            _preset_job["errors"] = errors

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    return {"started": True, "preset": name}

@app.get("/presets/{name}/progress")
def preset_progress(name: str):
    """Aktualny postęp ładowania presetu."""
    with _preset_lock:
        return dict(_preset_job)

@app.get("/dataset")
def get_dataset():
    files = state["uploaded_files"]
    class_counts = {}
    for v in files.values():
        class_counts[v["label"]] = class_counts.get(v["label"],0)+1
    return {"count":len(files),"classes":class_counts,
            "n_features":len(get_feature_names()),
            "ready_to_train": len(class_counts)>=2 and len(files)>=4}

@app.post("/train")
def train_model(params: TrainParams):
    files = state["uploaded_files"]
    if len(files) < 4:
        raise HTTPException(400,"Za mało plików. Wgraj co najmniej 4 sample.")
    X_all = np.array([v["features"] for v in files.values()])
    y_all = np.array([v["label"]    for v in files.values()])
    n = len(X_all)
    n_test = max(1, int(n * params.test_split))
    idx = np.random.permutation(n)
    X_train,y_train = X_all[idx[n_test:]], y_all[idx[n_test:]]
    X_test, y_test  = X_all[idx[:n_test]],  y_all[idx[:n_test]]
    if len(np.unique(y_train)) < 2:
        raise HTTPException(400,"Za mało różnych klas w danych treningowych.")
    model = DecisionTreeClassifier(
        criterion=params.criterion, max_depth=params.max_depth,
        min_samples_split=params.min_samples_split, min_samples_leaf=params.min_samples_leaf)
    t0 = time.time()
    model.fit(X_train, y_train, feature_names=get_feature_names())
    elapsed_ms = (time.time()-t0)*1000
    y_pred_test  = model.predict(X_test)
    y_pred_train = model.predict(X_train)
    tree_stats = {**model.count_nodes(),"depth":model.get_depth(),
                  "n_features":X_train.shape[1],"n_train":len(X_train),"n_test":len(X_test)}
    evaluation = evaluate_full(y_test,y_pred_test,classes=model.classes_,
                                tree_stats=tree_stats,training_time_ms=elapsed_ms)
    evaluation["train_accuracy"] = round(calc_accuracy(y_train,y_pred_train),4)
    state["model"] = model
    state["last_evaluation"] = evaluation
    state["tree_params"] = params.model_dump()
    return {"success":True,"tree":model.to_dict(),"evaluation":evaluation,
            "training_time_ms":round(elapsed_ms,2),
            "test_samples":{"y_true":y_test.tolist(),"y_pred":y_pred_test.tolist()}}

@app.get("/tree")
def get_tree():
    if state["model"] is None:
        raise HTTPException(400,"Drzewo nie zostało wytrenowane.")
    return {"tree":state["model"].to_dict(),"evaluation":state["last_evaluation"]}

@app.post("/predict")
async def predict_new(file: UploadFile = File(...)):
    if state["model"] is None:
        raise HTTPException(400,"Wytrenuj drzewo najpierw.")
    ext = Path(file.filename).suffix.lower()
    tmp_path = UPLOADS_DIR / f"tmp_{uuid.uuid4().hex[:6]}{ext}"
    with open(tmp_path,"wb") as f: shutil.copyfileobj(file.file,f)
    try:
        features = extract_features(str(tmp_path))
        waveform = get_waveform_data(str(tmp_path))
        predicted_class = state["model"].predict(features.reshape(1,-1))[0]
        probabilities   = state["model"].predict_proba(features.reshape(1,-1))[0]
    except Exception as e:
        raise HTTPException(500, f"Błąd predykcji: {e}")
    finally:
        tmp_path.unlink(missing_ok=True)
    return {"filename":file.filename,"predicted_class":predicted_class,
            "probabilities":probabilities,"waveform":waveform,
            "features":features.tolist(),"feature_names":get_feature_names()}

@app.get("/export")
def export_results():
    if state["model"] is None:
        raise HTTPException(400,"Brak modelu do eksportu.")
    data = {"export_date":datetime.now().isoformat(),
            "application":"Klasyfikator Sampli Perkusyjnych",
            "parameters":state["tree_params"],
            "tree":state["model"].to_dict(),
            "evaluation":state["last_evaluation"],
            "dataset_info":{"files":[{"filename":v["filename"],"label":v["label"]}
                                      for v in state["uploaded_files"].values()]}}
    fname = f"wynik_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    fpath = EXPORTS_DIR / fname
    with open(fpath,"w",encoding="utf-8") as f:
        json.dump(data,f,ensure_ascii=False,indent=2)
    return FileResponse(str(fpath), filename=fname, media_type="application/json")

@app.get("/health")
def health():
    return {"status":"ok","files_uploaded":len(state["uploaded_files"]),
            "model_trained":state["model"] is not None,
            "n_features":len(get_feature_names())}

# Serwuj pliki statyczne Vite (assets/, favicon itp.) — musi być NA KOŃCU
if STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
