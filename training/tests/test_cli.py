from pixel_training.cli import needs_login, parser


def test_a_gated_model_without_login_gets_the_login_hint():
    assert needs_login("OSError: Failed to load config from 'black-forest-labs/flux-3-image-klein'.")
    assert needs_login("401 Client Error")
    assert not needs_login("RuntimeError: MPS backend out of memory")


def test_tryout_runs_both_models_by_default():
    args = parser().parse_args(["tryout"])

    assert args.models == ["flux2-klein-4b", "flux3-klein"]
    assert (args.seeds, args.rotate, args.export) == (2, 4, "rotation-v1")
