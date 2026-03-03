using Microsoft.Maui.Storage;
using System;
using System.IO;
using System.Threading.Tasks;

namespace GarmentViewerApp;

public partial class MainPage : ContentView
{
    double _currentScale = 1;
    const double MaxScale = 10.0;   // 1000%
    const double MinScale = 0.05;

    public MainPage()
    {
        InitializeComponent();
    }

    async void OnSelectImageClicked(object sender, EventArgs e)
    {
        var result = await FilePicker.Default.PickAsync(new PickOptions
        {
            PickerTitle = "Select High Resolution Image",
            FileTypes = FilePickerFileType.Images
        });

        if (result == null)
            return;

        using var stream = await result.OpenReadAsync();

        var memoryStream = new MemoryStream();
        await stream.CopyToAsync(memoryStream);
        memoryStream.Position = 0;

        MainImage.Source = ImageSource.FromStream(() => memoryStream);

        await Task.Delay(100);
        FitToScreen();
    }

    void FitToScreen()
    {
        if (MainImage.Width <= 0 || MainImage.Height <= 0)
            return;

        var containerWidth = this.Width;
        var containerHeight = this.Height;

        if (containerWidth <= 0 || containerHeight <= 0)
            return;

        double scaleX = containerWidth / MainImage.Width;
        double scaleY = containerHeight / MainImage.Height;

        _currentScale = Math.Min(scaleX, scaleY);

        if (_currentScale > 1)
            _currentScale = 1;

        MainImage.Scale = _currentScale;

        UpdateZoomLabel();
    }

    void OnZoomInClicked(object sender, EventArgs e)
    {
        _currentScale += 0.5;
        if (_currentScale > MaxScale)
            _currentScale = MaxScale;

        MainImage.Scale = _currentScale;
        UpdateZoomLabel();
    }

    void OnZoomOutClicked(object sender, EventArgs e)
    {
        _currentScale -= 0.5;
        if (_currentScale < MinScale)
            _currentScale = MinScale;

        MainImage.Scale = _currentScale;
        UpdateZoomLabel();
    }

    void OnResetClicked(object sender, EventArgs e)
    {
        _currentScale = 1;
        MainImage.Scale = 1;
        UpdateZoomLabel();
    }

    void UpdateZoomLabel()
    {
        ZoomLabel.Text = $"Zoom: {(int)(_currentScale * 100)}%";
    }
    void OnFitClicked(object sender, EventArgs e)
{
    FitToScreen();
}

void OnRotateClicked(object sender, EventArgs e)
{
    MainImage.Rotation += 90;
}

void OnZoomSliderChanged(object sender, ValueChangedEventArgs e)
{
    MainImage.Scale = e.NewValue;
    ZoomLabel.Text = $"{(int)(e.NewValue * 100)}%";
}

void OnGridToggled(object sender, ToggledEventArgs e)
{
    if (e.Value)
        MainImage.Opacity = 0.9;
    else
        MainImage.Opacity = 1;
}
bool _isDark = true;

void OnToggleTheme(object sender, EventArgs e)
{
    if (_isDark)
    {
        Application.Current.Resources["PageBackground"] = Colors.White;
        Application.Current.Resources["PanelBackground"] = Color.FromArgb("#F3F3F3");
        Application.Current.Resources["HeaderBackground"] = Color.FromArgb("#EAEAEA");
        Application.Current.Resources["PrimaryText"] = Colors.Black;
        Application.Current.Resources["SecondaryText"] = Colors.DarkGray;
        Application.Current.Resources["AccentColor"] = Colors.Blue;
    }
    else
    {
        Application.Current.Resources["PageBackground"] = Color.FromArgb("#0E0E0E");
        Application.Current.Resources["PanelBackground"] = Color.FromArgb("#1A1A1A");
        Application.Current.Resources["HeaderBackground"] = Color.FromArgb("#141414");
        Application.Current.Resources["PrimaryText"] = Colors.White;
        Application.Current.Resources["SecondaryText"] = Colors.Gray;
        Application.Current.Resources["AccentColor"] = Color.FromArgb("#00FF88");
    }

    _isDark = !_isDark;
}

// // ================= TOOL MODES =================

// bool _markMode = false;
// bool _measureMode = false;
// bool _gridEnabled = false;
// int _rotation = 0;

// void OnMarkMode(object sender, EventArgs e)
// {
//     _markMode = !_markMode;
//     _measureMode = false;
// }

// void OnMeasureMode(object sender, EventArgs e)
// {
//     _measureMode = !_measureMode;
//     _markMode = false;
// }

// void OnGridToggle(object sender, EventArgs e)
// {
//     _gridEnabled = !_gridEnabled;

//     // Optional: force redraw overlay if you implement grid
// }


// void OnClearMarks(object sender, EventArgs e)
// {
//     if (OverlayCanvas != null)
//         OverlayCanvas.Drawable = null;
// }


// void OnBrightnessChanged(object sender, ValueChangedEventArgs e)
// {
//     // Placeholder – real brightness needs shader or image processing
// }
}



// using Microsoft.Maui.Storage;
// using System;
// using System.IO;

// namespace GarmentViewerApp;

// public partial class MainPage : ContentPage
// {
//     double _currentScale = 1;
//     const double MaxScale = 10.0;   // 1000%
//     const double MinScale = 0.05;

//     int _imageWidth;
//     int _imageHeight;

//     public MainPage()
//     {
//         InitializeComponent();
//     }

//   async void OnSelectImageClicked(object sender, EventArgs e)
// {
//     var result = await FilePicker.Default.PickAsync(new PickOptions
//     {
//         PickerTitle = "Select High Resolution Image",
//         FileTypes = FilePickerFileType.Images
//     });

//     if (result == null)
//         return;

//     using var stream = await result.OpenReadAsync();

//     var memoryStream = new MemoryStream();
//     await stream.CopyToAsync(memoryStream);
//     memoryStream.Position = 0;

//     MainImage.Source = ImageSource.FromStream(() => memoryStream);

//     await Task.Delay(100);
//     FitToScreen();
// }
//    void FitToScreen()
// {
//     _currentScale = 1;
//     MainImage.Scale = 1;

//     UpdateZoomLabel();
// }
//     void OnFitClicked(object sender, EventArgs e)
//     {
//         FitToScreen();
//     }

//     void OnZoomInClicked(object sender, EventArgs e)
//     {
//         _currentScale += 0.5;

//         if (_currentScale > MaxScale)
//             _currentScale = MaxScale;

//         MainImage.Scale = _currentScale;
//         UpdateZoomLabel();
//     }

//     void OnZoomOutClicked(object sender, EventArgs e)
//     {
//         _currentScale -= 0.5;

//         if (_currentScale < MinScale)
//             _currentScale = MinScale;

//         MainImage.Scale = _currentScale;
//         UpdateZoomLabel();
//     }

//     void OnResetClicked(object sender, EventArgs e)
//     {
//         _currentScale = 1;
//         MainImage.Scale = 1;
//         UpdateZoomLabel();
//     }

//     void UpdateZoomLabel()
//     {
//         ZoomLabel.Text = $"Zoom: {(int)(_currentScale * 100)}%";
//     }
// }




























// // using Microsoft.Maui.Storage;
// // using System;
// // using System.IO;

// // namespace GarmentViewerApp;

// // public partial class MainPage : ContentPage
// // {
// //     double _currentScale = 1;
// //     const double MaxScale = 4;   // 400%
// //     const double MinScale = 0.25; // 25%

// //     public MainPage()
// //     {
// //         InitializeComponent();
// //     }

// //     async void OnSelectImageClicked(object sender, EventArgs e)
// //     {
// //         var result = await FilePicker.Default.PickAsync(new PickOptions
// //         {
// //             PickerTitle = "Select High Resolution Image",
// //             FileTypes = FilePickerFileType.Images
// //         });

// //         if (result == null)
// //             return;

// //         var stream = await result.OpenReadAsync();
// //         MainImage.Source = ImageSource.FromStream(() => stream);

// //         _currentScale = 1;
// //         MainImage.Scale = 1;
// //         UpdateZoomLabel();
// //     }

// //     void OnZoomInClicked(object sender, EventArgs e)
// //     {
// //         _currentScale += 0.25;
// //         if (_currentScale > MaxScale)
// //             _currentScale = MaxScale;

// //         MainImage.Scale = _currentScale;
// //         UpdateZoomLabel();
// //     }

// //     void OnZoomOutClicked(object sender, EventArgs e)
// //     {
// //         _currentScale -= 0.25;
// //         if (_currentScale < MinScale)
// //             _currentScale = MinScale;

// //         MainImage.Scale = _currentScale;
// //         UpdateZoomLabel();
// //     }

// //     void OnResetClicked(object sender, EventArgs e)
// //     {
// //         _currentScale = 1;
// //         MainImage.Scale = 1;
// //         UpdateZoomLabel();
// //     }

// //     void UpdateZoomLabel()
// //     {
// //         ZoomLabel.Text = $"Zoom: {(int)(_currentScale * 100)}%";
// //     }
// // }








// // // using Microsoft.Maui.Storage;
// // // using System;
// // // using System.IO;

// // // namespace GarmentViewerApp;

// // // public partial class MainPage : ContentPage
// // // {
// // //     double _currentScale = 1;
// // //     double _startScale = 1;

// // //     public MainPage()
// // //     {
// // //         InitializeComponent();
// // //     }

// // //     async void OnSelectImageClicked(object sender, EventArgs e)
// // //     {
// // //         var result = await FilePicker.Default.PickAsync(new PickOptions
// // //         {
// // //             PickerTitle = "Select High Resolution Image",
// // //             FileTypes = FilePickerFileType.Images
// // //         });

// // //         if (result == null)
// // //             return;

// // //         var stream = await result.OpenReadAsync();
// // //         MainImage.Source = ImageSource.FromStream(() => stream);

// // //         var fileInfo = new FileInfo(result.FullPath);

// // //         ImageInfoLabel.Text = $"{fileInfo.Name} | {fileInfo.Length / 1024} KB";

// // //         _currentScale = 1;
// // //         MainImage.Scale = 1;
// // //         ZoomLabel.Text = "Zoom: 100%";
// // //     }

// // //     void OnPinchUpdated(object sender, PinchGestureUpdatedEventArgs e)
// // //     {
// // //         if (e.Status == GestureStatus.Started)
// // //         {
// // //             _startScale = MainImage.Scale;
// // //         }

// // //         if (e.Status == GestureStatus.Running)
// // //         {
// // //             _currentScale = _startScale * e.Scale;
// // //             _currentScale = Math.Max(1, Math.Min(_currentScale, 10));

// // //             MainImage.Scale = _currentScale;
// // //             ZoomLabel.Text = $"Zoom: {(int)(_currentScale * 100)}%";
// // //         }
// // //     }
// // // }




















// // // using Microsoft.Maui.Storage;
// // // using System;
// // // using System.IO;

// // // namespace GarmentViewerApp;

// // // public partial class MainPage : ContentPage
// // // {
// // //     double _currentScale = 1;
// // //     double _startScale = 1;
// // //     double _xOffset = 0;
// // //     double _yOffset = 0;

// // //     public MainPage()
// // //     {
// // //         InitializeComponent();
// // // 		MainImage.PointerWheelChanged += OnMouseWheelZoom;
// // //     }

// // // void OnMouseWheelZoom(object sender, PointerEventArgs e)
// // // {
// // //     var delta = e.GetCurrentPoint(MainImage).Properties.MouseWheelDelta;

// // //     if (delta > 0)
// // //         _currentScale += 0.1;
// // //     else
// // //         _currentScale -= 0.1;

// // //     _currentScale = Math.Max(1, Math.Min(_currentScale, 10));

// // //     MainImage.Scale = _currentScale;

// // //     ZoomLabel.Text = $"Zoom: {(int)(_currentScale * 100)}%";
// // // }
// // //     async void OnSelectImageClicked(object sender, EventArgs e)
// // //     {
// // //         var result = await FilePicker.Default.PickAsync(new PickOptions
// // //         {
// // //             PickerTitle = "Select High Resolution Image",
// // //             FileTypes = FilePickerFileType.Images
// // //         });

// // //         if (result == null)
// // //             return;

// // //         using var stream = await result.OpenReadAsync();
// // //         MainImage.Source = ImageSource.FromStream(() => stream);

// // //         var fileInfo = new FileInfo(result.FullPath);

// // //         ImageInfoLabel.Text = $"{fileInfo.Name} | {fileInfo.Length / 1024} KB";

// // //         _currentScale = 1;
// // //         MainImage.Scale = 1;
// // //         ZoomLabel.Text = "Zoom: 100%";
// // //     }

// // //     void OnPinchUpdated(object sender, PinchGestureUpdatedEventArgs e)
// // //     {
// // //         if (e.Status == GestureStatus.Started)
// // //         {
// // //             _startScale = MainImage.Scale;
// // //         }

// // //         if (e.Status == GestureStatus.Running)
// // //         {
// // //             _currentScale = _startScale * e.Scale;

// // //             _currentScale = Math.Max(1, Math.Min(_currentScale, 10));

// // //             MainImage.Scale = _currentScale;

// // //             ZoomLabel.Text = $"Zoom: {(int)(_currentScale * 100)}%";
// // //         }
// // //     }
// // // }

























// // // // using System.Net.Http;
// // // // using System.Net.Http.Headers;
// // // // using System.Text.Json;
// // // // using System.IO;

// // // // namespace GarmentViewerApp;
// // // // public partial class MainPage : ContentPage
// // // // {
// // // // 	 private string _selectedImagePath;

// // // //     public MainPage()
// // // //     {
// // // //         InitializeComponent();
// // // //         FabricPicker.SelectedIndex = 0;
// // // //         SizePicker.SelectedIndex = 1;
// // // //     }

// // // //   private async void OnPickImageClicked(object sender, EventArgs e)
// // // // {
// // // //     try
// // // //     {
// // // //         var result = await FilePicker.PickAsync();

// // // //         if (result != null)
// // // //         {
// // // //             _selectedImagePath = result.FullPath;
// // // //             await DisplayAlert("Selected", _selectedImagePath, "OK");
// // // //         }
// // // //         else
// // // //         {
// // // //             await DisplayAlert("Info", "No file selected.", "OK");
// // // //         }
// // // //     }
// // // //     catch (Exception ex)
// // // //     {
// // // //         await DisplayAlert("Error", ex.Message, "OK");
// // // //     }
// // // // }

// // // //     private async void OnProcessClicked(object sender, EventArgs e)
// // // //     {
// // // //         if (string.IsNullOrEmpty(_selectedImagePath))
// // // //         {
// // // //             await DisplayAlert("Error", "Select image first.", "OK");
// // // //             return;
// // // //         }

// // // //         Loader.IsVisible = true;
// // // //         Loader.IsRunning = true;

// // // //         try
// // // //         {
// // // //             var client = new HttpClient();

// // // //             using var content = new MultipartFormDataContent();

// // // //             var fileBytes = File.ReadAllBytes(_selectedImagePath);
// // // //             var fileContent = new ByteArrayContent(fileBytes);

// // // //             fileContent.Headers.ContentType =
// // // //                 MediaTypeHeaderValue.Parse("image/png");

// // // //             content.Add(fileContent, "file",
// // // //                 Path.GetFileName(_selectedImagePath));

// // // //             content.Add(new StringContent(FabricPicker.SelectedItem.ToString()), "fabric");
// // // //             content.Add(new StringContent(SizePicker.SelectedItem.ToString()), "size");
// // // //             content.Add(new StringContent(((int)DpiSlider.Value).ToString()), "dpi");

// // // //             var response = await client.PostAsync(
// // // //                 "http://127.0.0.1:8000/design/process",
// // // //                 content);

// // // //             var json = await response.Content.ReadAsStringAsync();

// // // //             if (!response.IsSuccessStatusCode)
// // // //             {
// // // //                 await DisplayAlert("API Error", json, "OK");
// // // //                 return;
// // // //             }

// // // //             var result = JsonDocument.Parse(json);
// // // //             var imageUrl = result.RootElement
// // // //                 .GetProperty("output_url").GetString();

// // // //             ResultImage.Source = ImageSource.FromUri(new Uri(imageUrl));
// // // //         }
// // // //         catch (Exception ex)
// // // //         {
// // // //             await DisplayAlert("Error", ex.Message, "OK");
// // // //         }
// // // //         finally
// // // //         {
// // // //             Loader.IsRunning = false;
// // // //             Loader.IsVisible = false;
// // // //         }
// // // //     }
// // // // }
