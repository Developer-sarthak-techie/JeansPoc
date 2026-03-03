using System.Text.Json;
using GarmentViewerApp.Dto;

namespace GarmentViewerApp.Services;

public static class RollMetadataService
{
    public static RollMetadata Load(string rollFolderPath)
    {
        var jsonPath = Path.Combine(rollFolderPath, "metadata.json");

        if (!File.Exists(jsonPath))
            throw new Exception("Metadata not found.");

        var json = File.ReadAllText(jsonPath);

        return JsonSerializer.Deserialize<RollMetadata>(json)!;
    }
}