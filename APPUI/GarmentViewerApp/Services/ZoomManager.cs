public static class ZoomManager
{
    public static int GetZoomLevel(double scale, int maxLevels)
    {
        if (scale >= 4) return 0;
        if (scale >= 2) return 1;
        if (scale >= 1) return 2;
        return Math.Min(3, maxLevels - 1);
    }
}