FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        git \
        build-essential \
        curl \
        pkg-config \
        libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Emscripten via emsdk
RUN git clone https://github.com/emscripten-core/emsdk.git /emsdk && \
    cd /emsdk && \
    git pull && \
    ./emsdk install latest && \
    ./emsdk activate latest && \
    echo 'source /emsdk/emsdk_env.sh' >> /root/.bashrc

# Install Rust toolchain
RUN curl https://sh.rustup.rs -sSf | sh -s -- -y && \
    rustup target add wasm32-unknown-unknown
ENV PATH="/root/.cargo/bin:/emsdk:/emsdk/upstream/emscripten:${PATH}"

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