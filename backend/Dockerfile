FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
COPY vendor /opt/vendor
RUN cd /opt/vendor && sha256sum -c SHA256SUMS
RUN pip install --no-cache-dir -r requirements.txt
RUN --network=none pip install --no-cache-dir --no-index --no-deps /opt/vendor/*.whl && pip check
COPY app app
COPY tests tests
RUN useradd --uid 10001 --create-home vault
USER vault
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
