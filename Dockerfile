FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        git \
        build-essential \
        curl \
        pkg-config \
        libssl-dev \
        emscripten \
    && rm -rf /var/lib/apt/lists/*

# Install Rust toolchain
RUN curl https://sh.rustup.rs -sSf | sh -s -- -y && \
    /root/.cargo/bin/rustup target add wasm32-unknown-unknown
ENV PATH="/root/.cargo/bin:${PATH}"

# Create app directory
WORKDIR /app

# Copy requirements and install Python deps
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . /app

# Expose default Gradio port
EXPOSE 7860

# Launch the Gradio app
CMD ["python", "app.py"]