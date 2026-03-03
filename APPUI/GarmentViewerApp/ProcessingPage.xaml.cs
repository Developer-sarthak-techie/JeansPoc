using System.Net.Http.Headers;

namespace GarmentViewerApp;

public partial class ProcessingPage : ContentView
{
    double _currentScale = 1;
    string _selectedSize = "30";
double _startScale = 0.1;

const double MinScale = 0.1;
const double MaxScale = 1000; // 1000%
    private string? _selectedFilePath;

    private readonly HttpClient _httpClient = new()
    {
        Timeout = TimeSpan.FromMinutes(10)
    };

    public ProcessingPage()
    {
        InitializeComponent();
    }

void OnSizeClicked(object sender, EventArgs e)
{
    // Reset all
    Size30.BackgroundColor = Color.FromArgb("#1E1E1E");
    Size32.BackgroundColor = Color.FromArgb("#1E1E1E");
    Size34.BackgroundColor = Color.FromArgb("#1E1E1E");

    var btn = sender as Button;

    if (btn != null)
    {
        btn.BackgroundColor = Color.FromArgb("#A50021");
        _selectedSize = btn.Text;
    }
}
    async void OnPickFileClicked(object sender, EventArgs e)
    {
        try
        {
            var result = await FilePicker.PickAsync(new PickOptions
            {
                PickerTitle = "Select Texture File",
                FileTypes = FilePickerFileType.Images
            });

            if (result != null)
            {
                _selectedFilePath = result.FullPath;
                SelectedFileLabel.Text = Path.GetFileName(_selectedFilePath);
            }
        }
        catch (Exception ex)
        {
            await ShowError(ex.Message);
        }
    }
  
  
  async void OnProcessClicked(object sender, EventArgs e)
{
    if (string.IsNullOrEmpty(_selectedFilePath))
    {
        await ShowError("Please select a texture file.");
        return;
    }

    if (string.IsNullOrEmpty(_selectedSize))
    {
        await ShowError("Please select a size.");
        return;
    }

    try
    {
        ProcessButton.IsEnabled = false;
        LoaderOverlay.IsVisible = true;

        //string size = SizePicker.SelectedItem.ToString()!;
string size = _selectedSize;
        using var content = new MultipartFormDataContent();

        var fileBytes = await File.ReadAllBytesAsync(_selectedFilePath);

        var fileContent = new ByteArrayContent(fileBytes);
        fileContent.Headers.ContentType =
            MediaTypeHeaderValue.Parse("image/png");

        content.Add(fileContent, "texture",
            Path.GetFileName(_selectedFilePath));

        content.Add(new StringContent(size), "size");

        var response = await _httpClient.PostAsync(
            "http://127.0.0.1:8000/design/engine/grade-imprint",
            content);

        response.EnsureSuccessStatusCode();

        var json = await response.Content.ReadAsStringAsync();

        var doc = System.Text.Json.JsonDocument.Parse(json);
        var root = doc.RootElement;

        if (root.GetProperty("status").GetString() == "success")
        {
            var relativePath = root.GetProperty("output").GetString();
            //var fullUrl = $"http://127.0.0.1:8000/{relativePath}";
var fullUrl = $"http://127.0.0.1:8000/{relativePath}?t={DateTime.Now.Ticks}";
ResultImage.Source = null; // Clear previous image
ResultImage.Source = ImageSource.FromUri(new Uri(fullUrl));
          
            ResultImage.Opacity = 0;
            ResultImage.Scale = 1;
            ResultImage.TranslationX = 0;
            ResultImage.TranslationY = 0;
            _currentScale = 1;
            ResultImage.Source = ImageSource.FromUri(new Uri(fullUrl));
            await Task.Delay(50); // allow layout pass

            FitToScreen();

            await ResultImage.FadeTo(1, 250);
        }
    }
    catch (Exception ex)
    {
        await ShowError(ex.Message);
    }
    finally
    {
        LoaderOverlay.IsVisible = false;
        ProcessButton.IsEnabled = true;
    }


    
}


void FitToScreen()
{
    if (ResultImage.Width <= 0 || ResultImage.Height <= 0)
        return;

    if (ImageContainer.Width <= 0 || ImageContainer.Height <= 0)
        return;

    double scaleX = ImageContainer.Width / ResultImage.Width;
    double scaleY = ImageContainer.Height / ResultImage.Height;

    _currentScale = Math.Min(scaleX, scaleY);

    if (_currentScale > 1)
        _currentScale = 1;

    ResultImage.Scale = _currentScale;

    UpdateZoomLabel();
}

void OnZoomInClicked(object sender, EventArgs e)
{
    _currentScale += 0.5;

    if (_currentScale > MaxScale)
        _currentScale = MaxScale;

    ResultImage.Scale = _currentScale;
    UpdateZoomLabel();
}

void UpdateZoomLabel()
{
    ZoomLabel.Text = $"Zoom: {(int)(_currentScale * 100)}%";
}
void OnZoomOutClicked(object sender, EventArgs e)
{
    _currentScale -= 0.5;

    if (_currentScale < MinScale)
        _currentScale = MinScale;

    ResultImage.Scale = _currentScale;
    UpdateZoomLabel();
}

void OnResetClicked(object sender, EventArgs e)
{
    _currentScale = 1;
    ResultImage.Scale = 1;
    UpdateZoomLabel();
}

void OnFitClicked(object sender, EventArgs e)
{
    FitToScreen();
}
void ResetTranslation()
{
    ResultImage.TranslationX = 0;
    ResultImage.TranslationY = 0;
}
void ApplyScale(double newScale)
{
    newScale = Math.Clamp(newScale, MinScale, MaxScale);

    _currentScale = newScale;
    ResultImage.Scale = _currentScale;
}
void OnPinchUpdated(object sender, PinchGestureUpdatedEventArgs e)
{
    if (e.Status == GestureStatus.Started)
    {
        _startScale = _currentScale;
    }
    else if (e.Status == GestureStatus.Running)
    {
        double newScale = _startScale * e.Scale;
        ApplyScale(newScale);
    }
}
    async Task ShowError(string message)
    {
        if (Application.Current?.MainPage != null)
            await Application.Current.MainPage.DisplayAlert("Error", message, "OK");
    }
}