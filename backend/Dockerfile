
COPY requirements.txt .

RUN python -m pip install --upgrade pip \
    && python -m pip install -r requirements.txt \
    && python -m pip uninstall -y msgpack setuptools urllib3 \
    && python -m pip install --no-cache-dir \
        "msgpack>=1.2.1" \
        "setuptools>=78.1.1" \
        "urllib3>=2.8.0" \
    && python -m pip check \
    && python -c "import msgpack, setuptools, urllib3; print('msgpack:', msgpack.__version__); print('setuptools:', setuptools.__version__); print('urllib3:', urllib3.__version__)"
