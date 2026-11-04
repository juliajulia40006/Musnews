
using Microsoft.EntityFrameworkCore;
using Musnews.Data;
using Musnews.Models;
using Xunit;

namespace Musnews.Tests;

public class TrackRepositoryTests
{
    private static AppDbContext GetDbContext()
    {
        var options = new DbContextOptionsBuilder<AppDbContext>()
            .UseSqlite("Data Source=:memory:")
            .Options;

        var context = new AppDbContext(options);

        context.Database.OpenConnection();
        context.Database.EnsureCreated();

        return context;
    }

    [Fact]
    public async Task AddAsync_ShouldAddTrack()
    {
        using var context = GetDbContext();

        // Создаём тестового пользователя.
        var user = new User
        {
            Username = "test_user",
            PasswordHash = "test_password_hash",
            CreatedAt = DateTime.UtcNow
        };

        context.Users.Add(user);
        await context.SaveChangesAsync();

        // Создаём трек, принадлежащий этому пользователю.
        var repo = new TrackRepository(context);

        var track = new Track
        {
            Title = "Test",
            Artist = "Tester",
            UserId = user.Id
        };

        await repo.AddAsync(track);

        // Проверяем сохранение трека.
        var all = await repo.GetAllAsync();
        var savedTrack = Assert.Single(all);

        Assert.Equal("Test", savedTrack.Title);
        Assert.Equal(user.Id, savedTrack.UserId);
    }
}
