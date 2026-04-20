using Microsoft.EntityFrameworkCore;
using Musnews.Data;
using Musnews.Models;

namespace Musnews.Tests;

public class TrackRepositoryTests
{
    private AppDbContext GetDbContext()
    {
        var options = new DbContextOptionsBuilder<AppDbContext>()
            .UseSqlite("DataSource=:memory:")
            .Options;
        var context = new AppDbContext(options);
        context.Database.OpenConnection();
        context.Database.EnsureCreated();
        return context;
    }

    [Fact]
    public async Task AddAsync_ShouldAddTrack()
    {

        var context = GetDbContext();
        var repo = new TrackRepository(context);
        var track = new Track { Title = "Test", Artist = "Tester" };

        await repo.AddAsync(track);

        var all = await repo.GetAllAsync();
        Assert.Single(all);
        Assert.Equal("Test", all.First().Title);
    }
}