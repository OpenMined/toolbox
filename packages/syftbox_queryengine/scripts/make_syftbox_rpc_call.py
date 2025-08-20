from fastsyftbox.direct_http_transport import SyftBoxSDK
from fastsyftbox.simple_client import SimpleRPCClient

sdk = SyftBoxSDK()

# res = asyncio.run(
#     sdk.syft_make_request(
#         "syft://koen@openmined.org/app_data/data-syncer/rpc/get_latest_file_to_sync/"
#     )
# )

client = SimpleRPCClient.for_syftbox_transport(
    app_owner="koen@openmined.org", app_name="data-syncer"
)

res = client.post("get_latest_file_to_sync/", json={})

print(res.json())

# transport = DirectSyftboxTransport(
#     app_owner="koen@openmined.org", app_name="data-syncer"
# )


# req = httpx.Request(
#     "POST",
#     "get_latest_file_to_sync/",
#     content=b"",
# )

# req = TranscriptionStoreRequest(
#     transcription="abc",
#     audio_chunk_id=1,
#     timestamp="2021-01-01T00:00:00Z",
#     user_email="koen@openmined.org",
#     device="MacBook Pro Microphone",
# )

# req = httpx.Request(
#     "POST",
#     "submit_transcription/",
#     content=req.model_dump_json().encode("utf-8"),
# )

# res = transport.handle_request(req)
# print(res.status_code)
# res.raise_for_status()
# print(res.json())
