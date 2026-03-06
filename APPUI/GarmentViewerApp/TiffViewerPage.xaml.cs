namespace GarmentViewerApp;

public partial class TiffViewerPage : ContentView
{
    private string? _selectedFilePath;

    double _currentScale = 1;
    double _startScale = 1;
    const double MinScale = 0.05;
    const double MaxScale = 50;

    private readonly HttpClient _httpClient = new()
    {
        Timeout = TimeSpan.FromSeconds(30)
    };

    public TiffViewerPage()
    {
        InitializeComponent();
    }

    async void OnPickFileClicked(object sender, EventArgs e)
    {
        try
        {
            var result = await FilePicker.PickAsync(new PickOptions
            {
                PickerTitle = "Select TIFF File",
                FileTypes = FilePickerFileType.Images
            });

            if (result == null) return;

            var ext = Path.GetExtension(result.FileName)?.ToLowerInvariant();
            if (ext != ".tiff" && ext != ".tif")
            {
                await ShowError("Please select a TIFF file (.tiff or .tif).");
                return;
            }

            _selectedFilePath = result.FullPath;
            var fileInfo = new FileInfo(_selectedFilePath);
            var sizeMB = fileInfo.Length / (1024.0 * 1024.0);
            SelectedFileLabel.Text = $"{result.FileName} ({sizeMB:F1} MB)";
            SelectedFileLabel.TextColor = Colors.White;

            await LoadTiffAsync();
        }
        catch (Exception ex)
        {
            await ShowError($"File picker error: {ex.Message}");
        }
    }

    async Task LoadTiffAsync()
    {
        if (string.IsNullOrEmpty(_selectedFilePath) || !File.Exists(_selectedFilePath))
            return;

        try
        {
            LoaderOverlay.IsVisible = true;
            EmptyState.IsVisible = true;
            ResolutionLegend.IsVisible = false;
            TiffImage.Source = null;

            TiffImage.Source = ImageSource.FromFile(_selectedFilePath);
            TiffImage.Opacity = 0;
            _currentScale = 1;
            TiffImage.Scale = 1;

            await Task.Delay(150);

            int width = 0, height = 0;
            try
            {
                var encodedPath = Uri.EscapeDataString(_selectedFilePath);
                var url = $"http://127.0.0.1:8000/design/engine/image-info?path={encodedPath}";
                var response = await _httpClient.GetAsync(url);
                if (response.IsSuccessStatusCode)
                {
                    var json = await response.Content.ReadAsStringAsync();
                    var doc = System.Text.Json.JsonDocument.Parse(json);
                    var root = doc.RootElement;
                    if (root.TryGetProperty("width", out var wEl) &&
                        root.TryGetProperty("height", out var hEl))
                    {
                        width = wEl.GetInt32();
                        height = hEl.GetInt32();
                    }
                }
            }
            catch
            {
                width = 0;
                height = 0;
            }

            EmptyState.IsVisible = false;
            LoaderOverlay.IsVisible = false;

            if (width > 0 && height > 0)
            {
                ResolutionLabel.Text = $"{width:N0} × {height:N0} px";
                ResolutionLegend.IsVisible = true;
            }
            else
            {
                ResolutionLabel.Text = "Resolution unknown";
                ResolutionLegend.IsVisible = true;
            }

            await Task.Delay(50);
            FitToScreen();
            await TiffImage.FadeTo(1, 200);
        }
        catch (Exception ex)
        {
            LoaderOverlay.IsVisible = false;
            await ShowError($"Failed to load image: {ex.Message}");
        }
    }

    void FitToScreen()
    {
        if (TiffImage.Width <= 0 || TiffImage.Height <= 0) return;
        if (ImageContainer.Width <= 0 || ImageContainer.Height <= 0) return;

        double scaleX = ImageContainer.Width / TiffImage.Width;
        double scaleY = ImageContainer.Height / TiffImage.Height;

        _currentScale = Math.Min(scaleX, scaleY);
        if (_currentScale > 1) _currentScale = 1;

        TiffImage.Scale = _currentScale;
        UpdateZoomLabel();
    }

    void OnZoomInClicked(object sender, EventArgs e)
    {
        _currentScale = Math.Min(_currentScale + 0.5, MaxScale);
        TiffImage.Scale = _currentScale;
        UpdateZoomLabel();
    }

    void OnZoomOutClicked(object sender, EventArgs e)
    {
        _currentScale = Math.Max(_currentScale - 0.5, MinScale);
        TiffImage.Scale = _currentScale;
        UpdateZoomLabel();
    }

    void OnFitClicked(object sender, EventArgs e) => FitToScreen();

    void OnPinchUpdated(object sender, PinchGestureUpdatedEventArgs e)
    {
        if (e.Status == GestureStatus.Started)
            _startScale = _currentScale;
        else if (e.Status == GestureStatus.Running)
        {
            _currentScale = Math.Clamp(_startScale * e.Scale, MinScale, MaxScale);
            TiffImage.Scale = _currentScale;
            UpdateZoomLabel();
        }
    }

    void UpdateZoomLabel()
    {
        ZoomLabel.Text = $"{(int)(_currentScale * 100)}%";
    }

    async Task ShowError(string message)
    {
        if (Application.Current?.MainPage != null)
            await Application.Current.MainPage.DisplayAlert("Error", message, "OK");
    }
}
