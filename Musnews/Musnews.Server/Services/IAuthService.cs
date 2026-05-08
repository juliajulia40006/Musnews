using Musnews.Models.DTO;

namespace Musnews.Server.Services
{
    public interface IAuthService
    {
        Task<AuthResponseDto> RegisterAsync(RegisterDto registerDto);
        Task<AuthResponseDto> LoginAsync(LoginDto loginDto);
        string HashPassword(string password);
        bool VerifyPassword(string password, string passwordHash);
    }
}