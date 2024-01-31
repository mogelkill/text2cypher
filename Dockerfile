FROM python:3.11 
EXPOSE 7860
WORKDIR /app
# Or any preferred Python version.
ADD src/ /app/src
ADD ui.py /app/

ADD requirements.txt /app/

RUN --mount=type=cache,target=/root/.cache/pip pip install -r requirements.txt

ENV PYTHONPATH "${PYTHONPATH}:/app/src"

CMD ["python", "/app/ui.py"] 
# Or enter the name of your unique directory and parameter set.