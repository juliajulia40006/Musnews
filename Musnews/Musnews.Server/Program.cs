using Microsoft.EntityFrameworkCore;
using SQLitePCL;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.IdentityModel.Tokens;
using System.Text;
using Musnews.Data;
using Musnews.Server.Services;

Batteries.Init();

var builder = WebApplication.CreateBuilder(args);

// Добавляем CORS для разработки
builder.Services.AddCors(options =>
{
    options.AddPolicy("AllowAll", policy =>
    {
        policy.AllowAnyOrigin()
              .AllowAnyMethod()
              .AllowAnyHeader();
    });
});

var jwtSecret = builder.Configuration["Jwt:Secret"] ?? "YourSuperSecretKeyThatIsAtLeast32CharactersLong!";
var key = Encoding.ASCII.GetBytes(jwtSecret);

builder.Services.AddAuthentication(options =>
{
    options.DefaultAuthenticateScheme = JwtBearerDefaults.AuthenticationScheme;
    options.DefaultChallengeScheme = JwtBearerDefaults.AuthenticationScheme;
})
.AddJwtBearer(options =>
{
    options.RequireHttpsMetadata = false; // Важно для разработки!
    options.SaveToken = true;
    options.TokenValidationParameters = new TokenValidationParameters
    {
        ValidateIssuerSigningKey = true,
        IssuerSigningKey = new SymmetricSecurityKey(key),
        ValidateIssuer = false,
        ValidateAudience = false,
        ClockSkew = TimeSpan.Zero
    };
});

builder.Services.AddAuthorization();
builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

// Используем SQLite с правильным подключением
builder.Services.AddDbContext<AppDbContext>(options =>
    options.UseSqlite("Data Source=music.db"));

builder.Services.AddScoped<ITrackRepository, TrackRepository>();
builder.Services.AddScoped<IAuthService, AuthService>();

// Добавляем поддержку статических файлов
builder.Services.AddSpaStaticFiles(configuration =>
{
    configuration.RootPath = "wwwroot";
});

var app = builder.Build();

// Автоматическая миграция при запуске
using (var scope = app.Services.CreateScope())
{
    var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();
    try
    {
        db.Database.Migrate();
    }
    catch (Exception ex)
    {
        Console.WriteLine($"Migration error: {ex.Message}");
    }
}

// В разработке используем HTTP (не HTTPS для простоты)
if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}
else
{
    app.UseHttpsRedirection();
}

app.UseCors("AllowAll");
app.UseStaticFiles(); // Для доступа к загруженным файлам
app.UseRouting();

app.UseAuthentication();
app.UseAuthorization();

// Настройка SPA - все запросы не к API идут на index.html
app.MapControllers();
app.MapFallbackToFile("index.html");

app.Run();