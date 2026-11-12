def main() -> None:
    import uvicorn

    uvicorn.run("knowledge_assistant.app:app", host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()
