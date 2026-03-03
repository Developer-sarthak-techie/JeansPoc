using Microsoft.Extensions.Logging;

namespace GarmentViewerApp;

public static class MauiProgram
{
	public static MauiApp CreateMauiApp()
	{
		var builder = MauiApp.CreateBuilder();
		builder
			.UseMauiApp<App>()
			.ConfigureFonts(fonts =>
			{
				fonts.AddFont("OpenSans-Regular.ttf", "OpenSansRegular");
				fonts.AddFont("OpenSans-Semibold.ttf", "OpenSansSemibold");
			});
			AppDomain.CurrentDomain.UnhandledException += (sender, e) =>
{
    System.Diagnostics.Debug.WriteLine("Unhandled: " + e.ExceptionObject);
};

#if DEBUG
		builder.Logging.AddDebug();
#endif

		return builder.Build();
	}
}
