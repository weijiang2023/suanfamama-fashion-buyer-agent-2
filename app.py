import streamlit as st
import random
import os
import uuid
import datetime
import json
import time
import pandas as pd

st.title("Hello, World!")
st.write("Welcome to your first Streamlit app!")

st.header("Upload an Image or Video for Fashion Scoring")

# Ensure uploads directory exists
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

uploaded_file = st.file_uploader("Choose an image or video", type=["jpg", "jpeg", "png", "mp4", "mov", "avi"])

# Use session state to store the machine score and file info
if 'last_file_id' not in st.session_state:
    st.session_state['last_file_id'] = None
if 'machine_score' not in st.session_state:
    st.session_state['machine_score'] = None
if 'base_filename' not in st.session_state:
    st.session_state['base_filename'] = None
if 'timestamp' not in st.session_state:
    st.session_state['timestamp'] = None
if 'unique_id' not in st.session_state:
    st.session_state['unique_id'] = None
if 'eval_start_time' not in st.session_state:
    st.session_state['eval_start_time'] = None
if 'delete_trigger' not in st.session_state:
    st.session_state['delete_trigger'] = 0

if uploaded_file is not None:
    file_type = uploaded_file.type
    # Generate a unique file id based on name and size
    file_id = f"{uploaded_file.name}_{uploaded_file.size}"
    # If a new file is uploaded, generate new machine score and file info
    if st.session_state['last_file_id'] != file_id:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:6]
        ext = os.path.splitext(uploaded_file.name)[-1]
        base_filename = f"{timestamp}_{unique_id}{ext}"
        st.session_state['timestamp'] = timestamp
        st.session_state['unique_id'] = unique_id
        st.session_state['base_filename'] = base_filename
        st.session_state['last_file_id'] = file_id
        st.session_state['machine_score'] = random.randint(0, 100)
        st.session_state['eval_start_time'] = time.time()  # Start timing
    # Use stored values
    timestamp = st.session_state['timestamp']
    unique_id = st.session_state['unique_id']
    base_filename = st.session_state['base_filename']
    score = st.session_state['machine_score']
    file_path = os.path.join(UPLOAD_DIR, base_filename)
    eval_start_time = st.session_state['eval_start_time']

    # Save the uploaded file (only if not already saved)
    if not os.path.exists(file_path):
        with open(file_path, "wb") as out_file:
            out_file.write(uploaded_file.getbuffer())

    # Display the file
    if file_type.startswith("image"):
        st.image(uploaded_file, caption="Uploaded Image", use_container_width=True)
    elif file_type.startswith("video"):
        st.video(uploaded_file)
    
    passing_score = 60
    
    # List of possible reasons
    reasons = [
        "Great color combination!",
        "Trendy style and fit.",
        "Classic look with modern touches.",
        "Unique accessories enhance the outfit.",
        "Bold fashion choice!",
        "Needs more color contrast.",
        "Try adding some accessories.",
        "Consider a different pattern or texture.",
        "Outfit could use more layering.",
        "Simple and elegant!"
    ]
    # Use a fixed reason per upload
    if 'reason' not in st.session_state or st.session_state['last_file_id'] != file_id:
        st.session_state['reason'] = random.choice(reasons)
    reason = st.session_state['reason']

    st.subheader(f"Machine Fashion Score: {score}")
    st.progress(score)
    
    if score >= passing_score:
        st.success(f"Pass! (Score ≥ {passing_score})")
    else:
        st.error(f"Not Passed (Score < {passing_score})")
    
    st.info(f"Reason: {reason}")

    # Fashion buyer can select their own score
    st.subheader("Fashion Buyer Score")
    buyer_score = st.slider(
        "Select your score as a fashion buyer:",
        min_value=0, max_value=100, value=score, key=f"buyer_score_slider_{base_filename}"
    )
    st.write(f"Fashion Buyer Score: {buyer_score}")
    st.progress(buyer_score)

    # Save button
    if st.button("Save Scores and Metadata"):
        score_diff = abs(score - buyer_score)
        eval_end_time = time.time()
        eval_duration = eval_end_time - eval_start_time if eval_start_time else None
        meta = {
            "filename": base_filename,
            "score": score,
            "buyer_score": buyer_score,
            "score_difference": score_diff,
            "passing_score": passing_score,
            "passed": score >= passing_score,
            "reason": reason,
            "timestamp": timestamp,
            "eval_duration": eval_duration
        }
        meta_filename = f"{timestamp}_{unique_id}.json"
        meta_path = os.path.join(UPLOAD_DIR, meta_filename)
        with open(meta_path, "w", encoding="utf-8") as meta_file:
            json.dump(meta, meta_file, ensure_ascii=False, indent=2)
        st.success(f"File and scores saved to '{UPLOAD_DIR}' directory. Score difference: {score_diff}")

# --- History Browsing Section ---

# Gather all .json metadata files in uploads/
history_entries = []
for fname in os.listdir(UPLOAD_DIR):
    if fname.endswith('.json'):
        meta_path = os.path.join(UPLOAD_DIR, fname)
        try:
            with open(meta_path, 'r', encoding='utf-8') as f:
                meta = json.load(f)
            # Find corresponding media file
            media_path = os.path.join(UPLOAD_DIR, meta.get('filename', ''))
            if os.path.exists(media_path):
                entry = {
                    'media_path': media_path,
                    'is_image': meta['filename'].lower().endswith(('.jpg', '.jpeg', '.png')),
                    'is_video': meta['filename'].lower().endswith(('.mp4', '.mov', '.avi')),
                    'score': meta.get('score'),
                    'buyer_score': meta.get('buyer_score'),
                    'score_difference': meta.get('score_difference'),
                    'timestamp': meta.get('timestamp'),
                    'reason': meta.get('reason'),
                    'eval_duration': meta.get('eval_duration'),
                    'meta_path': meta_path
                }
                history_entries.append(entry)
        except Exception as e:
            st.warning(f"Could not load metadata from {fname}: {e}")

# Sort by timestamp descending (most recent first)
history_entries.sort(key=lambda x: x['timestamp'], reverse=True)

# --- Summary Report ---
st.header("Summary Report")
total_evaluated = len(history_entries)
if total_evaluated > 0:
    avg_machine_score = sum(e['score'] for e in history_entries if e['score'] is not None) / total_evaluated
    avg_buyer_score = sum(e['buyer_score'] for e in history_entries if e['buyer_score'] is not None) / total_evaluated
    avg_difference = sum(e['score_difference'] for e in history_entries if e['score_difference'] is not None) / total_evaluated
    total_time = sum(e['eval_duration'] for e in history_entries if e.get('eval_duration') is not None)
    st.metric("Total Visuals Evaluated", total_evaluated)
    st.metric("Average Machine Score", f"{avg_machine_score:.2f}")
    st.metric("Average Buyer Score", f"{avg_buyer_score:.2f}")
    st.metric("Average Difference", f"{avg_difference:.2f}")
    st.metric("Total Evaluation Time (min)", f"{total_time/60:.2f}")

    # --- Line Plot of Scores ---
    df = pd.DataFrame({
        "Machine Score": [e['score'] for e in history_entries],
        "Buyer Score": [e['buyer_score'] for e in history_entries]
    })
    df = df[::-1].reset_index(drop=True)  # Most recent last, so x-axis is chronological
    st.line_chart(df)
else:
    st.info("No evaluations yet.")

# --- History Browsing Section ---
st.header("History of Evaluated Visuals")
for idx, entry in enumerate(history_entries):
    with st.container():
        col1, col2 = st.columns([1, 2])
        with col1:
            if entry['is_image']:
                st.image(entry['media_path'], width=120)
            elif entry['is_video']:
                st.video(entry['media_path'])
        with col2:
            st.metric("Machine Score", entry['score'])
            st.metric("Buyer Score", entry['buyer_score'])
            st.metric("Difference", entry['score_difference'])
            st.caption(f"Evaluated at: {entry['timestamp']}")
            st.caption(f"Reason: {entry['reason']}")
            if entry.get('eval_duration') is not None:
                st.caption(f"Evaluation Time: {entry['eval_duration']:.1f} sec")
            # Delete button
            delete_key = f"delete_{entry['meta_path']}"
            if st.button("Delete", key=delete_key):
                try:
                    os.remove(entry['meta_path'])
                    if os.path.exists(entry['media_path']):
                        os.remove(entry['media_path'])
                    st.session_state['delete_trigger'] += 1  # Trigger rerun
                    st.success("Record deleted.")
                except Exception as e:
                    st.error(f"Failed to delete: {e}")
        st.markdown("---")