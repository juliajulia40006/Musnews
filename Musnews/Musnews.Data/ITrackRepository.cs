using Musnews.Models;

namespace Musnews.Data
{
    public interface ITrackRepository
    {
        Task<IEnumerable<Track>> GetAllAsync();
        Task<IEnumerable<Track>> GetByUserIdAsync(int userId);
        Task<Track?> GetByIdAsync(int id);
        Task<Track> AddAsync(Track track);
        Task UpdateAsync(Track track);
        Task DeleteAsync(int id);
        Task<bool> UserOwnsTrackAsync(int trackId, int userId);
    }
}