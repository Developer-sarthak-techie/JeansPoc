using System.Net.Http.Headers;

namespace GarmentViewerApp.Services;

public class ApiService
{
    private readonly HttpClient _client;

    public ApiService()
    {
        _client = new HttpClient();
        _client.BaseAddress = new Uri("http://127.0.0.1:8000");
    }

    public async Task<string?> UploadForGrading(string imagePath, int size)
    {
        using var content = new MultipartFormDataContent();

        content.Add(new StringContent(size.ToString()), "size");

        var fileStream = File.OpenRead(imagePath);
        var fileContent = new StreamContent(fileStream);
        fileContent.Headers.ContentType = new MediaTypeHeaderValue("image/png");

        content.Add(fileContent, "file", Path.GetFileName(imagePath));

        var response = await _client.PostAsync("/engine/grade-imprint", content);

        if (!response.IsSuccessStatusCode)
            return null;

        var outputBytes = await response.Content.ReadAsByteArrayAsync();

        var outputPath = Path.Combine(FileSystem.CacheDirectory, "graded_output.tiff");
        await File.WriteAllBytesAsync(outputPath, outputBytes);

        return outputPath;
    }
}