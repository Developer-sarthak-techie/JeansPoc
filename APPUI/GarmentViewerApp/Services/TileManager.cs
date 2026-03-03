public static class TileManager
{
    public static (int startX, int endX, int startY, int endY)
        GetVisibleTiles(double offsetX,
                        double offsetY,
                        double viewportWidth,
                        double viewportHeight,
                        double scale,
                        int tileSize)
    {
        int startX = (int)Math.Floor(offsetX / (tileSize * scale));
        int startY = (int)Math.Floor(offsetY / (tileSize * scale));

        int endX = (int)Math.Ceiling((offsetX + viewportWidth) / (tileSize * scale));
        int endY = (int)Math.Ceiling((offsetY + viewportHeight) / (tileSize * scale));

        return (startX, endX, startY, endY);
    }
}