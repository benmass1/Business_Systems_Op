FROM python:3.9
WORKDIR /code
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt
COPY . .
# Hugging Face inasikiliza Port 7860
ENV PORT=7860
EXPOSE 7860
CMD ["gunicorn", "--bind", "0.0.0.0:7860", "run:app"]

