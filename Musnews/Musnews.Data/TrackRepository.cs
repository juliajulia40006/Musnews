using Microsoft.EntityFrameworkCore;
using Musnews.Models;

namespace Musnews.Data
{
    public class TrackRepository : ITrackRepository
    {
        private readonly AppDbContext _context;

        public TrackRepository(AppDbContext context)
        {
            _context = context;
        }

        public async Task<IEnumerable<Track>> GetAllAsync()
        {
            return await _context.Tracks.ToListAsync();
        }

        public async Task<IEnumerable<Track>> GetByUserIdAsync(int userId)
        {
            return await _context.Tracks
                .Where(t => t.UserId == userId)
                .ToListAsync();
        }

        public async Task<Track?> GetByIdAsync(int id)
        {
            return await _context.Tracks.FindAsync(id);
        }

        public async Task<Track> AddAsync(Track track)
        {
            _context.Tracks.Add(track);
            await _context.SaveChangesAsync();
            return track;
        }

        public async Task UpdateAsync(Track track)
        {
            _context.Tracks.Update(track);
            await _context.SaveChangesAsync();
        }

        public async Task DeleteAsync(int id)
        {
            var track = await _context.Tracks.FindAsync(id);
            if (track != null)
            {
                _context.Tracks.Remove(track);
                await _context.SaveChangesAsync();
            }
        }

        public async Task<bool> UserOwnsTrackAsync(int trackId, int userId)
        {
            return await _context.Tracks
                .AnyAsync(t => t.Id == trackId && t.UserId == userId);
        }
    }
}