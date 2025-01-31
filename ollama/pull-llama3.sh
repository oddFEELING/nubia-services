./bin/ollama serve &

pid=$!

sleep 5

echo "~~~~~~~~~~~~~~ Starting to pull model ~~~~~~~~~~~~~~"

ollama pull llama3.2

echo "~~~~~~~~~~~~~~ Pulled llama3.2 ~~~~~~~~~~~~~~"

wait $pid