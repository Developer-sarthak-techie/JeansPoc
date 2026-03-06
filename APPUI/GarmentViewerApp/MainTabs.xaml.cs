namespace GarmentViewerApp;

public partial class MainTabs : ContentPage
{
    private Border? _activeTab;   // nullable → fixes CS8618 warning

    public MainTabs()
    {
        InitializeComponent();

        AttachTab(DashboardTab, LoadDashboard);
        AttachTab(ProductsTab, LoadProducts);
        AttachTab(FeatureGradingTab, LoadFeatureGrading);
        AttachTab(TiffViewerTab, LoadTiffViewer);
        AttachTab(SettingsTab, LoadSettings);

        SetActiveTab(DashboardTab);
        LoadDashboard();
    }

    void AttachTab(Border tab, Action loadAction)
    {
        var tap = new TapGestureRecognizer();
        tap.Tapped += async (s, e) =>
        {
            SetActiveTab(tab);
            await AnimateContent(loadAction);
        };

        tab.GestureRecognizers.Add(tap);
    }

    void SetActiveTab(Border selectedTab)
    {
        if (_activeTab != null)
            _activeTab.BackgroundColor = Colors.Transparent;

        selectedTab.BackgroundColor = Color.FromArgb("#A50021");
        _activeTab = selectedTab;
    }

    async Task AnimateContent(Action loadAction)
    {
        await ContentArea.FadeTo(0, 120);
        loadAction();
        await ContentArea.FadeTo(1, 200);
    }

   void LoadDashboard()
{
    ContentArea.Content = new MainPage();
}

    void LoadProducts()
    {
        // ContentArea.Content = new Label
        // {
        //     Text = "Products Page",
        //     TextColor = Colors.White,
        //     HorizontalOptions = LayoutOptions.Center,
        //     VerticalOptions = LayoutOptions.Center
        // };
        ContentArea.Content = new ProcessingPage();
    }

    void LoadFeatureGrading()
    {
        ContentArea.Content = new FeatureGradingPage();
    }

    void LoadTiffViewer()
    {
        ContentArea.Content = new TiffViewerPage();
    }

    void LoadSettings()
    {
        ContentArea.Content = new Label
        {
            Text = "Settings Page",
            TextColor = Colors.White,
            HorizontalOptions = LayoutOptions.Center,
            VerticalOptions = LayoutOptions.Center
        };
    }
}