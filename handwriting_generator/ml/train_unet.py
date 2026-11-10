# -*- coding: utf-8 -*-
"""Train the lightweight glyph U-Net on printed->handwriting pairs.

Usage: python -m handwriting_generator.ml.train_unet <glyph_dir> <out_pt>
Built for <=4GB VRAM: batch=1, 128x128, optional AMP.
"""
import argparse
import time
from pathlib import Path

import torch
from torch.utils.data import DataLoader

from handwriting_generator.ml.dataset import GlyphPairDataset, GLYPH_SIZE
from handwriting_generator.ml.unet import GlyphUNet, count_params


def train(glyph_dir, out_pt, epochs=40, batch=1, lr=1e-3, device=None,
          amp=True, report_cb=None):
    device = device or ("cuda" if torch.cuda.is_available() else "cpu")
    ds = GlyphPairDataset(glyph_dir, size=GLYPH_SIZE)
    if len(ds) == 0:
        raise RuntimeError(f"没有可训练的配对数据：{glyph_dir} 下无 U+码点.png")

    model = GlyphUNet(1, 1, base=32).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=lr)
    dl = DataLoader(ds, batch_size=batch, shuffle=True, num_workers=0)
    scaler = torch.amp.GradScaler(enabled=(amp and device == "cuda"))

    def report(epoch, step, loss, n_total):
        if report_cb:
            report_cb(epoch, step, loss, n_total)

    print(f"[train_unet] device={device} params={count_params(model)/1e6:.2f}M pairs={len(ds)}")
    global_step = 0
    for epoch in range(1, epochs + 1):
        model.train()
        total_loss = 0.0
        n = 0
        for printed, hand, _ch in dl:
            printed = printed.to(device)
            hand = hand.to(device)
            with torch.amp.autocast(device_type=device, enabled=(amp and device == "cuda")):
                pred = model(printed)
                loss = torch.nn.functional.l1_loss(pred, hand)
            opt.zero_grad(set_to_none=True)
            scaler.scale(loss).backward()
            scaler.step(opt)
            scaler.update()
            total_loss += loss.item()
            n += 1
            global_step += 1
        avg = total_loss / max(1, n)
        print(f"[train_unet] epoch {epoch}/{epochs} loss={avg:.4f}")
        report(epoch, global_step, avg, len(ds))
        time.sleep(0.01)

    out = Path(out_pt)
    out.parent.mkdir(parents=True, exist_ok=True)
    torch.save({"model_state": model.state_dict(), "size": GLYPH_SIZE}, out)
    print(f"[train_unet] saved -> {out}")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("glyph_dir")
    ap.add_argument("out_pt")
    ap.add_argument("--epochs", type=int, default=40)
    ap.add_argument("--batch", type=int, default=1)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--cpu", action="store_true")
    args = ap.parse_args()
    device = "cpu" if args.cpu else None
    train(args.glyph_dir, args.out_pt, epochs=args.epochs, batch=args.batch,
          lr=args.lr, device=device)


if __name__ == "__main__":
    main()