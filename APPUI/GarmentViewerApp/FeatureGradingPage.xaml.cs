using System.Net.Http.Headers;
using System.Text.Json;

namespace GarmentViewerApp;

public partial class FeatureGradingPage : ContentView
{
    private string? _selectedFilePath;
    private string _selectedSize = "32";

    private string? _pngUrl;
    private string? _tiffUrl;
    private bool _showingPng = true;

    double _currentScale = 1;
    double _startScale = 1;
    const double MinScale = 0.05;
    const double MaxScale = 50;

    private readonly HttpClient _httpClient = new()
    {
        Timeout = TimeSpan.FromMinutes(30)
    };

    public FeatureGradingPage()
    {
        InitializeComponent();
    }

    // ============================================================
    // FILE PICKER
    // ============================================================

    async void OnPickFileClicked(object sender, EventArgs e)
    {
        try
        {
            var result = await FilePicker.PickAsync(new PickOptions
            {
                PickerTitle = "Select TIFF File (Size 30 Base)",
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
        }
        catch (Exception ex)
        {
            await ShowError($"File picker error: {ex.Message}");
        }
    }

    // ============================================================
    // SIZE SELECTION
    // ============================================================

    void OnSizeClicked(object sender, EventArgs e)
    {
        Size32Btn.BackgroundColor = Color.FromArgb("#1E1E1E");
        Size34Btn.BackgroundColor = Color.FromArgb("#1E1E1E");

        if (sender is Button btn)
        {
            btn.BackgroundColor = Color.FromArgb("#A50021");
            _selectedSize = btn.Text;
        }
    }

    // ============================================================
    // PROCESS GRADING
    // ============================================================

    async void OnProcessClicked(object sender, EventArgs e)
    {
        if (string.IsNullOrEmpty(_selectedFilePath))
        {
            await ShowError("Please select a TIFF file first.");
            return;
        }

        if (!File.Exists(_selectedFilePath))
        {
            await ShowError("Selected file no longer exists.");
            return;
        }

        try
        {
            ProcessButton.IsEnabled = false;
            LoaderOverlay.IsVisible = true;
            LoaderLabel.Text = "Processing...";
            StatusLabel.Text = "";

            using var content = new MultipartFormDataContent();

            content.Add(new StringContent(_selectedFilePath), "file_path");
            content.Add(new StringContent(_selectedSize), "size");
            content.Add(new StringContent("300"), "dpi");

            LoaderLabel.Text = "Processing grading... this may take a minute";

            var response = await _httpClient.PostAsync(
                "http://127.0.0.1:8000/design/engine/featureGrading",
                content);

            var json = await response.Content.ReadAsStringAsync();

            if (!response.IsSuccessStatusCode)
            {
                await ShowError($"Server error ({response.StatusCode}): {json}");
                return;
            }

            var doc = JsonDocument.Parse(json);
            var root = doc.RootElement;

            var status = root.GetProperty("status").GetString();
            if (status == "error")
            {
                var msg = root.GetProperty("message").GetString();
                await ShowError($"Processing failed: {msg}");
                return;
            }

            var tiffPath = root.GetProperty("tiff").GetString();
            var pngPath = root.GetProperty("preview").GetString();

            var cacheBuster = DateTime.Now.Ticks;
            _tiffUrl = $"http://127.0.0.1:8000/{tiffPath}?t={cacheBuster}";
            _pngUrl = $"http://127.0.0.1:8000/{pngPath}?t={cacheBuster}";

            EmptyState.IsVisible = false;
            ViewToggleContainer.IsVisible = true;

            _showingPng = true;
            SetToggleState();
            await LoadResultImage(_pngUrl);

            StatusLabel.Text = $"Graded to size {_selectedSize}";
            StatusLabel.TextColor = Color.FromArgb("#00FF88");
        }
        catch (TaskCanceledException)
        {
            await ShowError("Request timed out. The file may be too large.");
        }
        catch (HttpRequestException ex)
        {
            await ShowError($"Cannot reach server: {ex.Message}\nIs the backend running?");
        }
        catch (Exception ex)
        {
            await ShowError($"Error: {ex.Message}");
        }
        finally
        {
            LoaderOverlay.IsVisible = false;
            ProcessButton.IsEnabled = true;
        }
    }

    // ============================================================
    // PNG / TIFF TOGGLE
    // ============================================================

    async void OnTogglePng(object sender, EventArgs e)
    {
        if (_showingPng || string.IsNullOrEmpty(_pngUrl)) return;

        _showingPng = true;
        SetToggleState();
        StatusLabel.Text = "Loading PNG preview...";
        await LoadResultImage(_pngUrl);
        StatusLabel.Text = $"PNG preview - Size {_selectedSize}";
    }

    async void OnToggleTiff(object sender, EventArgs e)
    {
        if (!_showingPng || string.IsNullOrEmpty(_tiffUrl)) return;

        _showingPng = false;
        SetToggleState();
        StatusLabel.Text = "Loading full TIFF (may take a moment)...";
        await LoadResultImage(_tiffUrl);
        StatusLabel.Text = $"Full TIFF - Size {_selectedSize}";
    }

    void SetToggleState()
    {
        PngToggle.BackgroundColor = _showingPng
            ? Color.FromArgb("#A50021")
            : Color.FromArgb("#2D2D2D");
        TiffToggle.BackgroundColor = !_showingPng
            ? Color.FromArgb("#A50021")
            : Color.FromArgb("#2D2D2D");
    }

    // ============================================================
    // IMAGE LOADING AND DISPLAY
    // ============================================================

    async Task LoadResultImage(string url)
    {
        try
        {
            ResultImage.Source = null;
            ResultImage.Opacity = 0;
            _currentScale = 1;
            ResultImage.Scale = 1;
            ResultImage.TranslationX = 0;
            ResultImage.TranslationY = 0;

            ResultImage.Source = ImageSource.FromUri(new Uri(url));
            await Task.Delay(100);

            FitToScreen();
            await ResultImage.FadeTo(1, 200);
        }
        catch (Exception ex)
        {
            await ShowError($"Failed to load image: {ex.Message}");
        }
    }

    // ============================================================
    // ZOOM CONTROLS
    // ============================================================

    void FitToScreen()
    {
        if (ResultImage.Width <= 0 || ResultImage.Height <= 0) return;
        if (ImageContainer.Width <= 0 || ImageContainer.Height <= 0) return;

        double scaleX = ImageContainer.Width / ResultImage.Width;
        double scaleY = ImageContainer.Height / ResultImage.Height;

        _currentScale = Math.Min(scaleX, scaleY);
        if (_currentScale > 1) _currentScale = 1;

        ResultImage.Scale = _currentScale;
        UpdateZoomLabel();
    }

    void OnZoomInClicked(object sender, EventArgs e)
    {
        _currentScale = Math.Min(_currentScale + 0.5, MaxScale);
        ResultImage.Scale = _currentScale;
        UpdateZoomLabel();
    }

    void OnZoomOutClicked(object sender, EventArgs e)
    {
        _currentScale = Math.Max(_currentScale - 0.5, MinScale);
        ResultImage.Scale = _currentScale;
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
            ResultImage.Scale = _currentScale;
            UpdateZoomLabel();
        }
    }

    void UpdateZoomLabel()
    {
        ZoomLabel.Text = $"{(int)(_currentScale * 100)}%";
    }

    // ============================================================
    // HELPERS
    // ============================================================

    async Task ShowError(string message)
    {
        if (Application.Current?.MainPage != null)
            await Application.Current.MainPage.DisplayAlert("Error", message, "OK");
    }
}
