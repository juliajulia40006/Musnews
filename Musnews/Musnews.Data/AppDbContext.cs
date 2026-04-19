using Musnews.Models;
using System.Collections.Generic;
using Microsoft.EntityFrameworkCore;

namespace Musnews.Data
{
    public class AppDbContext : DbContext
    {
        public AppDbContext(DbContextOptions<AppDbContext> options) : base(options) { }

        public DbSet<Track> Tracks { get; set; }
        public DbSet<Playlist> Playlists { get; set; }
        public DbSet<User> Users { get; set; }
    }
}
