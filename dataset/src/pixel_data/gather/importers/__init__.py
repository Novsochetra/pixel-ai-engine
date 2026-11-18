from pixel_data.gather.importers import lpc_4view, pac

IMPORTERS = {
    "pac": pac.read,
    "lpc-4view": lpc_4view.read,
}
