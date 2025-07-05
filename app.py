import streamlit as st
import random
import os
import uuid
import datetime
import json

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
    # Use stored values
    timestamp = st.session_state['timestamp']
    unique_id = st.session_state['unique_id']
    base_filename = st.session_state['base_filename']
    score = st.session_state['machine_score']
    file_path = os.path.join(UPLOAD_DIR, base_filename)

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
        meta = {
            "filename": base_filename,
            "score": score,
            "buyer_score": buyer_score,
            "score_difference": score_diff,
            "passing_score": passing_score,
            "passed": score >= passing_score,
            "reason": reason,
            "timestamp": timestamp
        }
        meta_filename = f"{timestamp}_{unique_id}.json"
        meta_path = os.path.join(UPLOAD_DIR, meta_filename)
        with open(meta_path, "w", encoding="utf-8") as meta_file:
            json.dump(meta, meta_file, ensure_ascii=False, indent=2)
        st.success(f"File and scores saved to '{UPLOAD_DIR}' directory. Score difference: {score_diff}")