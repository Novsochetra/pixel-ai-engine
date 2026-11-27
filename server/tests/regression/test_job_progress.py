from pixel_server.job_view import progress_of

# Training logs "step N/M", not a tqdm bar, so its job showed only a spinner and no share done.
TRAINING_LOG = (
    "4,812 with the export's caption, 0 with an AI label (data/labels)\n"
    "step 1/400: loss 0.2311, 0.3% of the data (31.2s per step, ~207 min left)\n"
    "step 2/400: loss 0.2207, val 0.2150, saved, 0.5% of the data (30.9s per step, ~205 min left)\n"
)


def test_a_training_job_shows_its_share_of_steps_done():
    assert progress_of(TRAINING_LOG) == 0.005


def test_the_share_of_the_data_seen_is_not_read_as_progress():
    assert progress_of("loaded, 45.0% of the data seen so far") is None
