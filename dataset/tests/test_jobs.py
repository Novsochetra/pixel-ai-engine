from pixel_data.dashboard.jobs import default_command


# A plain `uv sync` in training/ takes the model packages out, and every job then failed at once
# with "No module named 'numpy'". Asking for the extra puts them back before a job starts.
def test_a_job_asks_uv_for_the_model_packages():
    command = default_command()
    run = command.index("run")

    assert command[run - 1 : run + 4] == ["uv", "run", "--extra", "models", "pixel-train"]
