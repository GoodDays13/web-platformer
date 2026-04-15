FROM python:slim
 
WORKDIR /app
 
RUN pip install --no-cache-dir websockets
 
COPY . .
 
EXPOSE 8765
 
CMD ["python", "server.py"]
