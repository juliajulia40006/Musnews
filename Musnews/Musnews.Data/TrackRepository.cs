using Microsoft.EntityFrameworkCore;
using Musnews.Models;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace Musnews.Data
{
    public class TrackRepository : ITrackRepository
    {
        private readonly AppDbContext _context;
        public TrackRepository(AppDbContext context) => _context = context;

        public async Task<IEnumerable<Track>> GetAllAsync()
            => await _context.Tracks.ToListAsync();

        public async Task<Track?> GetByIdAsync(int id)
            => await _context.Tracks.FindAsync(id);

        public async Task AddAsync(Track track)
        {
            await _context.Tracks.AddAsync(track);
            await _context.SaveChangesAsync();
        }
    }
}
