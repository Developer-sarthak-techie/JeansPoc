namespace GarmentViewerApp.Dto;

public class RollMetadata
{
    public string roll_id { get; set; } = string.Empty;
    public int width_px { get; set; }
    public int height_px { get; set; }
    public int tile_size { get; set; }
    public int tiles_x { get; set; }
    public int tiles_y { get; set; }
     // 🔥 Add this
    public List<int> zoom_levels { get; set; } = new();
}