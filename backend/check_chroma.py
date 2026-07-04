import chromadb

client = chromadb.PersistentClient(path="chroma_db")
collection = client.get_or_create_collection(name="documents")

data = collection.get()

print("Total vectors:", len(data["ids"]))

for i in range(min(10, len(data["ids"]))):
    print("ID:", data["ids"][i])
    print("Metadata:", data["metadatas"][i])
    print()