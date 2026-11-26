from pixel_data.gather.importers import landscapes, lpc_4view, lpc_action, moss_64, pac, pixellab, single_pictures

IMPORTERS = {
    "pac": pac.read,
    "lpc-4view": lpc_4view.read,
    "lpc-action": lpc_action.read,
    "moss-64": moss_64.read,
    "pixellab": pixellab.read,
    "atlas-1.4m": single_pictures.read,
    "icons-172k": single_pictures.read,
    "pixelart-308k": single_pictures.read,
    "landscapes-20k": landscapes.read,
}
