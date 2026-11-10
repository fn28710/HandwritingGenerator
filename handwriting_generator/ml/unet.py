# -*- coding: utf-8 -*-
"""Lightweight conditional U-Net for handwriting style transfer.

Input:  printed glyph image (1 or 3 channel) + optional style seed
Output: handwriting glyph image (1 channel ink on transparent, or 3 channel)
Designed for <= 4GB VRAM: ~5M params, trains at batch=1..4 on 128x128 glyphs.
"""
import math

import torch
import torch.nn as nn


def _double_conv(in_c, out_c):
    return nn.Sequential(
        nn.Conv2d(in_c, out_c, 3, padding=1, bias=False),
        nn.BatchNorm2d(out_c),
        nn.ReLU(inplace=True),
        nn.Conv2d(out_c, out_c, 3, padding=1, bias=False),
        nn.BatchNorm2d(out_c),
        nn.ReLU(inplace=True),
    )


class GlyphUNet(nn.Module):
    """Small U-Net: printed glyph -> handwriting glyph (same resolution)."""

    def __init__(self, in_ch=1, out_ch=1, base=32):
        super().__init__()
        self.in_ch = in_ch
        self.out_ch = out_ch

        self.down1 = _double_conv(in_ch, base)
        self.down2 = _double_conv(base, base * 2)
        self.down3 = _double_conv(base * 2, base * 4)
        self.down4 = _double_conv(base * 4, base * 8)

        self.pool = nn.MaxPool2d(2)

        self.bottleneck = _double_conv(base * 8, base * 16)

        self.up4 = nn.ConvTranspose2d(base * 16, base * 8, 2, stride=2)
        self.conv4 = _double_conv(base * 16, base * 8)
        self.up3 = nn.ConvTranspose2d(base * 8, base * 4, 2, stride=2)
        self.conv3 = _double_conv(base * 8, base * 4)
        self.up2 = nn.ConvTranspose2d(base * 4, base * 2, 2, stride=2)
        self.conv2 = _double_conv(base * 4, base * 2)
        self.up1 = nn.ConvTranspose2d(base * 2, base, 2, stride=2)
        self.conv1 = _double_conv(base * 2, base)

        self.head = nn.Conv2d(base, out_ch, 1)

    def forward(self, x):
        d1 = self.down1(x)
        p1 = self.pool(d1)
        d2 = self.down2(p1)
        p2 = self.pool(d2)
        d3 = self.down3(p2)
        p3 = self.pool(d3)
        d4 = self.down4(p3)
        p4 = self.pool(d4)

        b = self.bottleneck(p4)

        u4 = self.up4(b)
        u4 = self._crop_to(u4, d4)
        c4 = self.conv4(torch.cat([u4, d4], dim=1))

        u3 = self.up3(c4)
        u3 = self._crop_to(u3, d3)
        c3 = self.conv3(torch.cat([u3, d3], dim=1))

        u2 = self.up2(c3)
        u2 = self._crop_to(u2, d2)
        c2 = self.conv2(torch.cat([u2, d2], dim=1))

        u1 = self.up1(c2)
        u1 = self._crop_to(u1, d1)
        c1 = self.conv1(torch.cat([u1, d1], dim=1))

        return self.head(c1)

    @staticmethod
    def _crop_to(a, b):
        """Center-crop a to match spatial size of b."""
        dh = a.size(2) - b.size(2)
        dw = a.size(3) - b.size(3)
        top = dh // 2
        left = dw // 2
        return a[:, :, top:top + b.size(2), left:left + b.size(3)]


def count_params(model):
    return sum(p.numel() for p in model.parameters())


if __name__ == "__main__":
    m = GlyphUNet(1, 1, base=32)
    print("params (millions):", count_params(m) / 1e6)
    x = torch.randn(1, 1, 128, 128)
    y = m(x)
    print("in", tuple(x.shape), "-> out", tuple(y.shape))